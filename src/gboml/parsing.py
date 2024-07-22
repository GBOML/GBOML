import pathlib
from itertools import repeat

from lark import Lark, Tree, tree, Token, Transformer, v_args
from gboml.ast import *
from typing import Optional, Tuple, Iterable
from collections import namedtuple

from gboml.tools.tree_modifier import visit


def _op_transform(op): return lambda *x, meta: ExpressionOp(op, list(x), meta=meta)
def _bool_op_transform(op): return lambda *x, meta: BoolExpressionOp(op, list(x), meta=meta)
def _insert_genobj_below_loops(loop: Loop | None, generated_obj: GeneratedObjectsType) -> GeneratedObjectsType:
    if loop is None:
        return generated_obj
    childloop = loop
    while childloop.child is not None:
        childloop = childloop.child
    childloop.child = generated_obj
    return loop

def _isinstance_obj_below_loops(obj: GBOMLObject, type: type) -> bool:
    while isinstance(obj, Loop):
        obj = obj.child
    return isinstance(obj, type)

def gen_meta(meta: tree.Meta) -> Meta: return MetaNone if meta.empty else Meta(line=meta.line, column=meta.column, filename=None)


def _vargs(f, _, children, meta):
    """ Wrapper for methods in GBOMLLarkTransformer """
    return f(gen_meta(meta), *children)


default_lark_def = open((pathlib.Path(__file__).parent / "gboml.lark").resolve()).read()


class GBOMLParser:
    def __init__(self, lark_def=default_lark_def):
        self.lark_def = lark_def
        self.parser = Lark(self.lark_def, start="start", parser="lalr", propagate_positions=True)


    def parse_file(self, filename: str) -> GBOMLGraph:
        """
        Args:
            filename: path to the GBOML-formatted text to parse
        Returns: a GBOMLGraph
        """
        with open(filename) as f:
            return self.parse(f.read(), filename)


    def parse(self, text: str, filename: Optional[str] = None) -> GBOMLGraph:
        """
        Args:
            text: GBOML-formatted text to parse
            filename: filename to indicate in the metadata of GBOMLGraph
        Returns: a GBOMLGraph
        """
        lark_tree: Tree = self.parser.parse(text)
        return self._lark_to_gboml(lark_tree, filename)

    def _lark_to_gboml(self, tree: Tree, filename: Optional[str] = None) -> GBOMLGraph:
        out_tree = self._lark_to_gboml_transformer().transform(tree)
        if filename is not None:
            def update_meta(obj: GBOMLObject):
                if obj.meta:
                    obj.meta.filename = filename
            out_tree = visit(out_tree, {GBOMLObject: update_meta})
        return out_tree

    def _lark_to_gboml_transformer(self) -> Transformer:
        """
            Converts a Lark-parsed Tree of a GBOML file to our own AST format.
        """

        return self.GBOMLLarkTransformer()

    @v_args(wrapper=_vargs)
    class GBOMLLarkTransformer(Transformer):
            """ Transforms the Lark-parsed tree to a GBOMLGraph instance """

            #
            # These rules will be converted to lists
            #
            as_list = {
                "objectives_block", "constraints_block",
                "parameters_block", "global_block", "olist", "mlist", "node_redefs",
                "hyperedge_redefs", "separated_list", "separated_maybe_empty_list"
            }

            as_sets = {
                "tags"
            }

            #
            # These rules will be converted to the given object, by calling
            # obj(*children, meta=meta)
            #
            to_obj = {
                "path_root": PathRoot,
                "subtraction": _op_transform(Operator.minus),
                "sum": _op_transform(Operator.plus),
                "exponent": _op_transform(Operator.exponent),
                "product": _op_transform(Operator.times),
                "division": _op_transform(Operator.divide),
                "modulo": _op_transform(Operator.modulo),
                "unary_minus": _op_transform(Operator.unary_minus),
                "function_call": ExpressionFunctionCall,
                "dot_call": ExpressionDotCall,
                "array_call": ExpressionArrayCall,
                "bool_expression_and": _bool_op_transform(Operator.b_and),
                "bool_expression_or": _bool_op_transform(Operator.b_or),
                "bool_expression_not": _bool_op_transform(Operator.b_not),
                "bool_expression_comparison": BoolExpressionComparison,
                "import": ImportFile,
                "variable_scope_change": ScopeChange,
                "range": Range,
                "array": Array,
                "dict": Dictionary,
                "definition_indexing_param": IndexingParameterDefinition,
                "ctr_activate": lambda *x, meta: CtrActivation(ActivationType.activate, *x, meta=meta),
                "ctr_deactivate": lambda *x, meta: CtrActivation(ActivationType.deactivate, *x, meta=meta),
                "obj_activate": lambda *x, meta: ObjActivation(ActivationType.activate, *x, meta=meta),
                "obj_deactivate": lambda *x, meta: ObjActivation(ActivationType.deactivate, *x, meta=meta),
                "extends": Extends,
                "variable_name": lambda *x, meta: x
            }

            def __default__(self, data, children, meta):
                if data in self.as_list:
                    return list(children)
                if data in self.as_sets:
                    return set(children)
                if data in self.to_obj:
                    return self.to_obj[data](*children, meta=gen_meta(meta))
                raise RuntimeError(f"Unknown rule {data}")

            #
            # Other rules that need to be manually managed
            #
            def INT(self, token): return int(token.value)
            def FLOAT(self, token): return float(token.value)
            def ID(self, token): return token.value
            def TAG(self, token): return token.value
            def SCOPE(self, token): return VarScope(token.value)
            def CTR_OPERATOR(self, token): return Operator(token.value)
            def OBJ_TYPE(self, token): return ObjType(token.value)
            def COMPARISON_OPERATOR(self, token): return Operator(token.value)
            def STRING(self, token): return token.value[1:-1].replace('\\"', '"')
            def VTYPE(self, token): return VarType(token.value)
            def DEF_TYPE(self, token): return DefinitionType(token.value)

            NodesAndHyperEdges = namedtuple("NodesAndHyperEdges", ["nodes", "hyperedges"])

            def program_block(self, meta: Meta, *childrens: list[Node | HyperEdge]) -> NodesAndHyperEdges:
                return self.NodesAndHyperEdges([x for x in childrens if _isinstance_obj_below_loops(x, Node)], [x for x in childrens if _isinstance_obj_below_loops(x, HyperEdge)])

            def hyperedge_definition(self, meta: Meta, name: str, indices: list[str], extends: Optional[Extends],
                                     loop: Optional[Loop], tags: set[str], param_block: list[Definition] = None,
                                     constraint_block: list[Constraint | CtrActivation] = None):
                constraint_block = constraint_block or []
                activations = [x for x in constraint_block if _isinstance_obj_below_loops(x, CtrActivation)]
                constraint_block = [x for x in constraint_block if _isinstance_obj_below_loops(x, Constraint)]
                param_block = param_block or []

                if loop is not None and not indices:
                    raise Exception(f"Generated hyperedge {name} needs brackets for declaration.")
                hyperedge = HyperEdgeDefinition(name, indices, extends, param_block, constraint_block, activations, tags, meta=meta)
                return _insert_genobj_below_loops(loop, hyperedge)

            def node_definition(self, meta: Meta, name: str, indices: list[str], extends: Optional[Extends],
                                loop: Optional[Loop], tags: set[str],
                                param_block: list[Definition] = None, subprogram_block: NodesAndHyperEdges = None,
                                variable_block: list[VariableDefinition] = None,
                                constraint_block: list[Constraint | CtrActivation] = None,
                                objectives_block: list[Objective | ObjActivation] = None):
                objectives_block = objectives_block or []
                constraint_block = constraint_block or []
                variable_block = variable_block or []
                param_block = param_block or []
                subprogram_block = subprogram_block or self.NodesAndHyperEdges([], [])

                activations: list[Activation] = [x for x in constraint_block if _isinstance_obj_below_loops(x, CtrActivation)] + [x for x in objectives_block if _isinstance_obj_below_loops(x, ObjActivation)]
                constraint_block = [x for x in constraint_block if _isinstance_obj_below_loops(x, Constraint)]
                objectives_block = [x for x in objectives_block if _isinstance_obj_below_loops(x, Objective)]

                if loop is not None and not indices:
                    raise Exception(f"Generated node {name} needs brackets for declaration.")

                node = NodeDefinition(name, indices, extends, param_block,
                                        subprogram_block.nodes, subprogram_block.hyperedges,
                                        variable_block, constraint_block,
                                        objectives_block, activations, tags, meta=meta)
                return _insert_genobj_below_loops(loop, node)

            def node_import(self, meta: Meta, name: str, imported_name: Path, imported_from: str, redef: list[ScopeChange | Definition]):
                return NodeDefinition(name, [], Extends(imported_name, imported_from, meta=meta),
                                      parameters=[x for x in redef if _isinstance_obj_below_loops(x, Definition)],
                                      variables=[x for x in redef if _isinstance_obj_below_loops(x, ScopeChange)],
                                      meta=meta)

            def hyperedge_import(self, meta: Meta, name: str, imported_name: Path, imported_from: str, redef: list[Definition]):
                return HyperEdgeDefinition(name, [], Extends(imported_name, imported_from, meta=meta),
                                           parameters=redef, meta=meta)

            def start(self, meta: Meta, time_horizon: Optional[int], global_defs: list[Definition], nodes_hyperedges: NodesAndHyperEdges):
                return GBOMLGraph(time_horizon, global_defs, nodes_hyperedges.nodes, nodes_hyperedges.hyperedges, meta=meta)

            def variable_definition(self, meta: Meta, scope: VarScope, type: Optional[VarType], names: list[(str, list[Expression])],
                                    imports_from: Optional[list[Path]],
                                    bound_lower: Optional[Expression], bound_upper: Optional[Expression], tags: set[str]):
                if imports_from is not None and len(imports_from) != len(names):
                    raise Exception("Invalid variable import, numbers of variables on the left and on the right-side of "
                                    "`<-` don't match")
                for name, import_from in zip(names, imports_from or repeat(None, len(names))):
                    yield VariableDefinition(name[0], name[1], scope, type or VarType.continuous,
                                             bound_lower, bound_upper, import_from, tags, meta=meta)

            def variables_block(self, _: Meta, *defs: Tuple[Iterable[VariableDefinition]]):
                return [vd for iterable in defs for vd in iterable]

            def array_or_dict(self, meta: Meta, entries: list[PossiblyGeneratedExpression | DictEntry]):
                if all(_isinstance_obj_below_loops(x, DictEntry) for x in entries):
                    return Dictionary(entries, meta=meta)
                if all(not _isinstance_obj_below_loops(x, DictEntry) for x in entries):
                    return Array(entries, meta=meta)
                raise Exception("An array cannot contain dictionary entries (and conversely)")

            def definition_std_param(self, meta: Meta, name: str, args: Optional[list[str]], typ: DefinitionType, val: Expression, tags: set[str]):
                if args is not None:
                    if typ != DefinitionType.expression:
                        raise Exception("Functions can only be defined as expressions (use `<-` instead of `=`)")
                    return FunctionDefinition(name, args, val, tags, meta=meta)
                elif typ == DefinitionType.expression:
                    return ExpressionDefinition(name, val, tags, meta=meta)
                else:
                    return ConstantDefinition(name, val, tags, meta=meta)

            def constraint(self, meta: Meta, name: Optional[str], expr: Expression, loop: Optional[Loop], tags: set[str]):
                if _isinstance_obj_below_loops(expr, BoolExpressionComparison):
                    if expr.operator not in [Operator.lesser_or_equal, Operator.greater_or_equal, Operator.equal]:
                        print(expr.operator)
                        raise Exception("Comparisons in constraints can only be done using <=, >=, or ==")
                    return _insert_genobj_below_loops(loop, StdConstraint(name, expr.lhs, expr.operator, expr.rhs, tags, meta=meta))
                if _isinstance_obj_below_loops(expr, ExpressionFunctionCall):
                    return _insert_genobj_below_loops(loop, FunctionConstraint(name, expr.lhs, expr.operands, tags, meta=meta))
                raise Exception("Not a valid constraint; it should be either a comparison or a function call")

            def base_loop(self, meta: Meta, varid: str, on: Expression, condition: Optional[Expression], childloop: Optional[Loop] = None):
                return BaseLoop(childloop, varid, on, condition, meta=meta)

            def like_loop(self, meta: Meta, varid: str, on: Path, condition: Optional[Expression], childloop: Optional[Loop] = None):
                return LikeLoop(childloop, varid, on, condition, meta=meta)

            def implicit_loop(self, meta: Meta, condition: Optional[Expression], childloop: Optional[Loop] = None):
                return ImplicitLoop(childloop, condition, meta=meta)

            def generated_expression(self, meta: Meta, value: Expression, loop: Loop):
                return _insert_genobj_below_loops(loop, GeneratedExpression(value, meta=meta))

            def objective(self, meta: Meta, type: ObjType, name: Optional[str], expression: Expression, loop: Optional[Loop], tags: set[str]):
                return _insert_genobj_below_loops(loop, Objective(type, name, expression, tags))

            def dict_entry(self, meta: Meta, key: Expression, value: Expression, loop: Optional[Loop]):
                return _insert_genobj_below_loops(loop, DictEntry(key, value))
