import pathlib
from itertools import repeat

from lark import Lark, Tree, Token, Transformer, v_args
from gboml.ast import *
from typing import Optional, Tuple, Iterable
from collections import namedtuple

from gboml.tools.tree_modifier import modify, visit


def _op_transform(op): return lambda *x, meta: ExpressionOp(op, list(x), meta=meta)
def _bool_op_transform(op): return lambda *x, meta: BoolExpressionOp(op, list(x), meta=meta)
def gen_meta(lark_token: Token) -> Meta: return Meta(line=lark_token.line, column=lark_token.column, filename=None)


def _vargs(f, data, children, _meta):
    """ Wrapper for methods in GBOMLLarkTransformer """
    return f(gen_meta(data), *children)

class GBOMLParser:
    def __init__(self):
        self.lark_def = (pathlib.Path(__file__).parent / "gboml.lark")
        self.parser = Lark(open(self.lark_def.resolve()).read(), start="start", parser="lalr")


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
                "var_or_param_leaf": VarOrParamLeaf,
                "var_or_param": VarOrParam,
                "constraint_std": StdConstraint,
                "constraint_sos": SOSConstraint,
                "objective": Objective,
                "base_loop": BaseLoop,
                "eq_loop": EqLoop,
                "implicit_loop": ImplicitLoop,
                "subtraction": _op_transform(Operator.minus),
                "sum": _op_transform(Operator.plus),
                "exponent": _op_transform(Operator.exponent),
                "product": _op_transform(Operator.times),
                "division": _op_transform(Operator.divide),
                "modulo": _op_transform(Operator.modulo),
                "unary_minus": _op_transform(Operator.unary_minus),
                "bool_expression_and": _bool_op_transform(Operator.b_and),
                "bool_expression_or": _bool_op_transform(Operator.b_or),
                "bool_expression_not": _bool_op_transform(Operator.b_not),
                "bool_expression_comparison": BoolExpressionComparison,
                "function": Function,
                "import": ImportFile,
                "variable_scope_change": ScopeChange,
                "generated_rvalue": GeneratedRValue,
                "range": Range,
                "dict_entry": DictEntry,
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

            def __default__(self, data, children, _):
                if data in self.as_list:
                    return list(children)
                if data in self.as_sets:
                    return set(children)
                if data in self.to_obj:
                    return self.to_obj[data](*children, meta=gen_meta(data))
                raise RuntimeError(f"Unknown rule {data}")

            #
            # Other rules that need to be manually managed
            #
            def INT(self, token): return int(token.value)
            def FLOAT(self, token): return float(token.value)
            def ID(self, token): return token.value
            def TAG(self, token): return token.value
            def SCOPE(self, token): return VarScope(token.value)
            def SOS_TYPE(self, token): return SOSType(token.value)
            def CTR_OPERATOR(self, token): return Operator(token.value)
            def OBJ_TYPE(self, token): return ObjType(token.value)
            def COMPARISON_OPERATOR(self, token): return Operator(token.value)
            def STRING(self, token): return token.value[1:-1].replace('\\"', '"')
            def VTYPE(self, token): return VarType(token.value)
            def DEF_TYPE(self, token): return DefinitionType(token.value)

            NodesAndHyperEdges = namedtuple("NodesAndHyperEdges", ["nodes", "hyperedges"])

            def program_block(self, meta: Meta, *childrens: list[Node | HyperEdge]) -> NodesAndHyperEdges:
                return self.NodesAndHyperEdges([x for x in childrens if isinstance(x, Node)], [x for x in childrens if isinstance(x, HyperEdge)])

            def hyperedge_definition(self, meta: Meta, name: str, indices: list[str], extends: Optional[Extends],
                                     loop: Optional[Loop], tags: set[str], param_block: list[Definition] = None,
                                     constraint_block: list[Constraint | CtrActivation] = None):
                constraint_block = constraint_block or []
                activations = [x for x in constraint_block if isinstance(x, CtrActivation)]
                constraint_block = [x for x in constraint_block if isinstance(x, Constraint)]
                param_block = param_block or []

                if loop is None:
                    return HyperEdgeDefinition(name, extends, param_block, constraint_block,
                                               activations, tags, meta=meta)
                else:
                    if len(indices) == 0:
                        raise Exception(f"Invalid name for node: {name}")
                    return HyperEdgeGenerator(name, indices, loop, extends, param_block, constraint_block,
                                              activations, tags, meta=meta)

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

                activations: list[Activation] = [x for x in constraint_block if isinstance(x, CtrActivation)] + [x for x in objectives_block if isinstance(x, ObjActivation)]
                constraint_block = [x for x in constraint_block if isinstance(x, Constraint)]
                objectives_block = [x for x in objectives_block if isinstance(x, Objective)]

                if loop is None:
                    return NodeDefinition(name, extends, param_block,
                                          subprogram_block.nodes, subprogram_block.hyperedges,
                                          variable_block, constraint_block,
                                          objectives_block, activations, tags, meta=meta)
                else:
                    if len(indices) == 0:
                        raise Exception(f"Invalid name for node: {name}")
                    return NodeGenerator(name, indices, loop, extends, param_block,
                                         subprogram_block.nodes, subprogram_block.hyperedges,
                                         variable_block, constraint_block,
                                         objectives_block, activations, tags, meta=meta)

            def node_import(self, meta: Meta, name: str, imported_name: VarOrParam, imported_from: str, redef: list[ScopeChange | Definition]):
                return NodeDefinition(name, Extends(imported_name, imported_from, meta=meta),
                                      parameters=[x for x in redef if isinstance(x, Definition)],
                                      variables=[x for x in redef if isinstance(x, ScopeChange)],
                                      meta=meta)

            def hyperedge_import(self, meta: Meta, name: str, imported_name: VarOrParam, imported_from: str, redef: list[Definition]):
                return HyperEdgeDefinition(name, Extends(imported_name, imported_from, meta=meta),
                                           parameters=redef, meta=meta)

            def start(self, meta: Meta, time_horizon: Optional[int], global_defs: list[Definition], nodes_hyperedges: NodesAndHyperEdges):
                return GBOMLGraph(time_horizon, global_defs, nodes_hyperedges.nodes, nodes_hyperedges.hyperedges, meta=meta)

            def variable_definition(self, meta: Meta, scope: VarScope, type: Optional[VarType], names: list[(str, list[str])],
                                    imports_from: Optional[list[VarOrParam]],
                                    bound_lower: Optional[Expression], bound_upper: Optional[Expression], tags: set[str]):
                if imports_from is not None and len(imports_from) != len(names):
                    raise Exception("Invalid variable import, numbers of variables on the left and on the right-side of "
                                    "`<-` don't match")
                for name, import_from in zip(names, imports_from or repeat(None, len(names))):
                    yield VariableDefinition(name[0], name[1], scope, type or VarType.continuous,
                                             bound_lower, bound_upper, import_from, tags, meta=meta)

            def variables_block(self, _: Meta, *defs: Tuple[Iterable[VariableDefinition]]):
                return [vd for iterable in defs for vd in iterable]

            def multi_loop(self, meta: Meta, *loops: Tuple[Loop]):
                return MultiLoop(list(loops), meta=meta)

            def array_or_dict(self, meta: Meta, entries: list[RValueWithGen | DictEntry]):
                if all(isinstance(x, DictEntry) for x in entries):
                    return Dictionary(entries, meta=meta)
                if all(not isinstance(x, DictEntry) for x in entries):
                    return Array(entries, meta=meta)
                raise Exception("An array cannot contain dictionary entries (and conversely)")

            def definition_std_param(self, meta: Meta, name: str, args: Optional[list[str]], typ: DefinitionType, val: RValue, tags: set[str]):
                if args is not None:
                    if typ != DefinitionType.expression:
                        raise Exception("Functions can only be defined as expressions (use `<-` instead of `=`)")
                    return FunctionDefinition(name, args, val, tags, meta=meta)
                elif typ == DefinitionType.expression:
                    return ExpressionDefinition(name, val, tags, meta=meta)
                else:
                    return ConstantDefinition(name, val, tags, meta=meta)