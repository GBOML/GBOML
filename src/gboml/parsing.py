import pathlib
import dataclasses
from itertools import repeat

from lark import Lark, Tree, tree, Token, Transformer, v_args
from gboml.ast import *
from gboml.reserved_definitions import GBOML_RESERVED_DEFINITIONS
from typing import Optional, Iterable, NamedTuple

from gboml.tools.tree_modifier import visit


def _op_transform(op): return lambda *x, meta: ExpressionOp(op, x, meta=meta)
def _bool_op_transform(op): return lambda *x, meta: BoolExpressionOp(op, x, meta=meta)
def _insert_genobj_below_loops(loop: Optional[Loop], generated_obj: GeneratedObjectsType) -> GeneratedObjectsType|Loop:
    if loop is None:
        return generated_obj
    return dataclasses.replace(loop, child=_insert_genobj_below_loops(loop.child, generated_obj))

def _isinstance_obj_below_loops(obj: GBOMLObject, _type: type | tuple[type, ...]) -> bool:
    while isinstance(obj, Loop):
        obj = obj.child
    return isinstance(obj, _type)

def _childlists_to_tuples(it): return map(lambda c: tuple(c) if isinstance(c, list) else c, it)

def _gen_meta(meta: tree.Meta) -> Optional[Meta]: return None if meta.empty else Meta(line=meta.line, column=meta.column, filename=None)


def _vargs(f, _, children, meta):
    """ Wrapper for methods in GBOMLLarkTransformer """
    return f(_gen_meta(meta), *_childlists_to_tuples(children))


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
                if obj.meta is not None:
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
            as_tuple = {
                "objectives_block", "constraints_block",
                "parameters_block", "global_block", "olist", "mlist", "node_redefs",
                "hyperedge_redefs", "separated_list", "separated_maybe_empty_list"
            }

            as_frozenset = {
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
                if data in self.as_tuple:
                    return tuple(children)
                if data in self.as_frozenset:
                    return frozenset(children)
                if data in self.to_obj:
                    return self.to_obj[data](*_childlists_to_tuples(children), meta=_gen_meta(meta))
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

            NodesAndHyperEdges = NamedTuple("NodesAndHyperEdges", nodes=tuple[Loop | NodeDefinition], hyperedges=tuple[Loop | HyperEdgeDefinition])

            def program_block(self, meta: Meta, *childrens: tuple[NodeDefinition | HyperEdgeDefinition]) -> NodesAndHyperEdges:
                return self.NodesAndHyperEdges(tuple(x for x in childrens if _isinstance_obj_below_loops(x, NodeDefinition)), tuple(x for x in childrens if _isinstance_obj_below_loops(x, HyperEdgeDefinition)))

            def hyperedge_definition(self, meta: Meta, name: str, extends: Optional[Extends], tags: frozenset[str],
                                     param_block: tuple[Definition] = None, constraint_block: tuple[Constraint | CtrActivation] = None):
                return self.hyperedge_definition_gen(meta, name, tuple(), extends, None, tags, param_block, constraint_block)

            def hyperedge_definition_gen(self, meta: Meta, name: str, indices: tuple[str], extends: Optional[Extends],
                                         loop: Optional[Loop], tags: frozenset[str], param_block: tuple[Definition] = None,
                                         constraint_block: tuple[Constraint | CtrActivation] = None):
                constraint_block = constraint_block or tuple()
                activations = tuple(x for x in constraint_block if _isinstance_obj_below_loops(x, CtrActivation))
                constraint_block = tuple(x for x in constraint_block if _isinstance_obj_below_loops(x, Constraint))
                param_block = param_block or tuple()

                if loop is not None and not indices:
                    raise Exception(f"{meta}: Generated hyperedge {name} needs brackets for declaration.")
                hyperedge = HyperEdgeDefinition(name, indices, extends, param_block, constraint_block, activations, tags, meta=meta)
                return _insert_genobj_below_loops(loop, hyperedge)

            def node_definition(self, meta: Meta, name: str, extends: Optional[Extends], tags: frozenset[str],
                                param_block: tuple[Definition] = None, subprogram_block: NodesAndHyperEdges = None,
                                variable_block: tuple[VariableDefinition] = None,
                                constraint_block: tuple[Constraint | CtrActivation] = None,
                                objectives_block: tuple[Objective | ObjActivation] = None):
                return self.node_definition_gen(meta, name, tuple(), extends, None, tags, param_block, subprogram_block, variable_block, constraint_block, objectives_block)

            def node_definition_gen(self, meta: Meta, name: str, indices: tuple[str], extends: Optional[Extends],
                                    loop: Optional[Loop], tags: frozenset[str],
                                    param_block: tuple[Definition] = None, subprogram_block: NodesAndHyperEdges = None,
                                    variable_block: tuple[VariableDefinition] = None,
                                    constraint_block: tuple[Constraint | CtrActivation] = None,
                                    objectives_block: tuple[Objective | ObjActivation] = None):
                objectives_block = objectives_block or tuple()
                constraint_block = constraint_block or tuple()
                variable_block = variable_block or tuple()
                param_block = param_block or tuple()
                subprogram_block = subprogram_block or self.NodesAndHyperEdges(tuple(), tuple())

                activations = tuple(x for x in constraint_block if _isinstance_obj_below_loops(x, CtrActivation)) + tuple(x for x in objectives_block if _isinstance_obj_below_loops(x, ObjActivation))
                constraint_block = tuple(x for x in constraint_block if _isinstance_obj_below_loops(x, Constraint))
                objectives_block = tuple(x for x in objectives_block if _isinstance_obj_below_loops(x, Objective))

                if loop is not None and not indices:
                    raise Exception(f"{meta}: Generated node {name} needs brackets for declaration.")

                node = NodeDefinition(name, indices, extends, param_block, subprogram_block.nodes, subprogram_block.hyperedges,
                                      variable_block, constraint_block, objectives_block, activations, tags, meta=meta)
                return _insert_genobj_below_loops(loop, node)

            def node_import(self, meta: Meta, name: str, imported_name: Path, imported_from: str, redef: tuple[ScopeChange | Definition]):
                return NodeDefinition(name, tuple(), Import(imported_name, imported_from, meta=meta),
                                      parameters=tuple(x for x in redef if _isinstance_obj_below_loops(x, Definition)),
                                      variables=tuple(x for x in redef if _isinstance_obj_below_loops(x, ScopeChange)),
                                      meta=meta)

            def hyperedge_import(self, meta: Meta, name: str, imported_name: Path, imported_from: str, redef: tuple[Definition]):
                return HyperEdgeDefinition(name, tuple(), Import(imported_name, imported_from, meta=meta), parameters=redef, meta=meta)

            def start(self, meta: Meta, time_horizon: Optional[int], global_defs: tuple[Definition], nodes_hyperedges: NodesAndHyperEdges):
                if time_horizon is None:
                    reserved_defs = filter(lambda defi: defi.name not in ['t','T'], GBOML_RESERVED_DEFINITIONS)
                else:
                    reserved_defs = map(lambda defi: defi if defi.name != 'T' else dataclasses.replace(defi, value=time_horizon), GBOML_RESERVED_DEFINITIONS)
                return GBOMLGraph(tuple(reserved_defs), time_horizon, global_defs, nodes_hyperedges.nodes, nodes_hyperedges.hyperedges, meta=meta)

            def _variable_definition(self, meta: Meta, scope: VarScope, _type: Optional[VarType], names: tuple[(str, list[Expression])],
                                    imports_from: Optional[tuple[Path]],
                                    bound_lower: Optional[Expression], bound_upper: Optional[Expression], tags: frozenset[str]):
                if imports_from is not None and len(imports_from) != len(names):
                    raise Exception(f"{meta}: Invalid variable import, numbers of variables on the left and on the right-side of `<-` don't match")
                for name, import_from in zip(names, imports_from or repeat(None, len(names))):
                    yield VariableDefinition(name[0], tuple(name[1]), scope, _type or VarType.continuous,
                                             bound_lower, bound_upper, import_from, tags, meta=meta)

            def variable_definition_std(self, meta: Meta, scope: VarScope, _type: Optional[VarType], names: tuple[(str, list[Expression])], tags: frozenset[str]):
                yield from self._variable_definition(meta, scope, _type, names, None, None, None, tags)

            def variable_definition_arrow(self, meta: Meta, scope: VarScope, _type: Optional[VarType], names: tuple[(str, list[Expression])],
                                    imports_from: Optional[tuple[Path]], tags: frozenset[str]):
                yield from self._variable_definition(meta, scope, _type, names, imports_from, None, None, tags)

            def variable_definition_limit(self, meta: Meta, scope: VarScope, _type: Optional[VarType], names: tuple[(str, list[Expression])],
                                    bound_lower: Optional[Expression], bound_upper: Optional[Expression], tags: frozenset[str]):
                yield from self._variable_definition(meta, scope, _type, names, None, bound_lower, bound_upper, tags)

            def variables_block(self, _: Meta, *defs: tuple[Iterable[VariableDefinition]]):
                return tuple(vd for iterable in defs for vd in iterable)

            def array_or_dict(self, meta: Meta, entries: tuple[PossiblyGeneratedExpression | DictEntry]):
                if all(_isinstance_obj_below_loops(x, DictEntry) for x in entries):
                    return Dictionary(entries, meta=meta)
                if all(not _isinstance_obj_below_loops(x, DictEntry) for x in entries):
                    return Array(entries, meta=meta)
                raise Exception(f"{meta}: An array cannot contain dictionary entries (and conversely)")

            def definition_std_param(self, meta: Meta, name: str, args: Optional[tuple[str]], typ: DefinitionType, val: Expression, tags: frozenset[str]):
                if args is not None:
                    if typ != DefinitionType.expression:
                        raise Exception(f"{meta}: Functions can only be defined as expressions (use `<-` instead of `=`)")
                    return FunctionDefinition(name, args, val, tags, meta=meta)
                elif typ == DefinitionType.expression:
                    return ExpressionDefinition(name, val, tags, meta=meta)
                else:
                    return ConstantDefinition(name, val, tags, meta=meta)

            def constraint(self, meta: Meta, name: Optional[str], expr: Expression, loop: Optional[Loop], tags: frozenset[str]):
                if isinstance(expr, BoolExpressionComparison):
                    if expr.operator not in (Operator.lesser_or_equal, Operator.greater_or_equal, Operator.equal):
                        raise Exception(f"{meta}: Comparisons in constraints can only be done using <=, >=, or ==")
                    return _insert_genobj_below_loops(loop, StdConstraint(name, expr.lhs, expr.operator, expr.rhs, tags, meta=meta))
                if isinstance(expr, ExpressionFunctionCall) and expr.lhs.name in map(lambda f: f.name, filter(lambda f: isinstance(f, FunctionConstraintDefinition), GBOML_RESERVED_DEFINITIONS)) and loop is None:
                    return FunctionConstraint(name, expr.lhs, expr.operands, tags, meta=meta)
                raise Exception(f"{meta}: Not a valid constraint; it should be either a function call to FunctionConstraintDefinition without loop or a comparison")

            def base_loop(self, meta: Meta, varid: str, on: Expression, condition: Optional[Expression], childloop: Optional[Loop] = None):
                return BaseLoop(childloop, varid, on, condition, meta=meta)

            def like_loop(self, meta: Meta, varid: str, on: Path, condition: Optional[Expression], childloop: Optional[Loop] = None):
                return LikeLoop(childloop, varid, on, condition, meta=meta)

            def implicit_loop(self, meta: Meta, condition: Optional[Expression], childloop: Optional[Loop] = None):
                return ImplicitLoop(childloop, condition, meta=meta)

            def generated_expression(self, meta: Meta, value: Expression, loop: Loop):
                return _insert_genobj_below_loops(loop, GeneratedExpression(value, meta=meta))

            def objective(self, meta: Meta, _type: ObjType, name: Optional[str], expression: Expression, loop: Optional[Loop], tags: frozenset[str]):
                return _insert_genobj_below_loops(loop, Objective(_type, name, expression, tags, meta=meta))

            def dict_entry(self, meta: Meta, key: Expression, value: Expression, loop: Optional[Loop]):
                return _insert_genobj_below_loops(loop, DictEntry(key, value, meta=meta))
