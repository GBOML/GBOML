import pathlib
from itertools import repeat

from lark import Lark, Tree, Token, Transformer, v_args
from gboml.ast import *
from typing import Optional, Tuple, Iterable
from collections import namedtuple

parser = Lark(open((pathlib.Path(__file__).parent / "gboml.lark").resolve()).read(), start="start", parser="lalr")


def parse_file(filename: str) -> GBOMLGraph:
    """
    Args:
        filename: path to the GBOML-formatted text to parse
    Returns: a GBOMLGraph
    """
    with open(filename) as f:
        return parse(f.read(), filename)


def parse(text: str, filename: Optional[str] = None) -> GBOMLGraph:
    """
    Args:
        text: GBOML-formatted text to parse
        filename: filename to indicate in the metadata of GBOMLGraph
    Returns: a GBOMLGraph
    """
    lark_tree: Tree = parser.parse(text)
    return _lark_to_gboml(lark_tree, filename)


def _lark_to_gboml(tree: Tree, filename: Optional[str] = None) -> GBOMLGraph:
    """
        Converts a Lark-parsed Tree of a GBOML file to our own AST format.
    """
    def op_transform(op): return lambda *x, meta: ExpressionOp(op, list(x), meta=meta)
    def bool_op_transform(op): return lambda *x, meta: BoolExpressionOp(op, list(x), meta=meta)

    def gen_meta(lark_token: Token) -> Meta:
        return Meta(line=lark_token.line, column=lark_token.column, filename=filename)

    def _vargs(f, data, children, _meta):
        """ Wrapper for methods in GBOMLLarkTransformer """
        return f(gen_meta(data), *children)

    @v_args(wrapper=_vargs)
    class GBOMLLarkTransformer(Transformer):
        """ Transforms the Lark-parsed tree to a GBOMLGraph instance """

        #
        # These rules will be converted to lists
        #
        as_list = {
            "objectives_block", "constraints_block",
            "parameters_block", "global_block", "olist", "mlist", "node_redefs",
            "hyperedge_redefs", "separated_list", "separated_maybe_empty_list",
            "tags"
        }

        #
        # These rules will be converted to the given object, by calling
        # obj(*children, meta=meta)
        #
        to_obj = {
            "hyperedge_import": HyperEdgeImport,
            "var_or_param_leaf": VarOrParamLeaf,
            "var_or_param": VarOrParam,
            "constraint_std": StdConstraint,
            "constraint_sos": SOSConstraint,
            "objective": Objective,
            "base_loop": BaseLoop,
            "implicit_loop": ImplicitLoop,
            "subtraction": op_transform(Operator.minus),
            "sum": op_transform(Operator.plus),
            "exponent": op_transform(Operator.exponent),
            "product": op_transform(Operator.times),
            "division": op_transform(Operator.divide),
            "modulo": op_transform(Operator.modulo),
            "unary_minus": op_transform(Operator.unary_minus),
            "bool_expression_and": bool_op_transform(Operator.b_and),
            "bool_expression_or": bool_op_transform(Operator.b_or),
            "bool_expression_not": bool_op_transform(Operator.b_not),
            "bool_expression_comparison": BoolExpressionComparison,
            "function": Function,
            "import": ImportFile,
            "variable_scope_change": ScopeChange,
            "generated_rvalue": GeneratedRValue,
            "range": Range,
            "dict_entry": DictEntry,
            "array": Array,
            "dict": Dictionary,
            "ctr_activate": lambda *x, meta: CtrActivation(ActivationType.activate, *x, meta=meta),
            "ctr_deactivate": lambda *x, meta: CtrActivation(ActivationType.deactivate, *x, meta=meta),
            "obj_activate": lambda *x, meta: ObjActivation(ActivationType.activate, *x, meta=meta),
            "obj_deactivate": lambda *x, meta: ObjActivation(ActivationType.deactivate, *x, meta=meta),
            "extends": Extends
        }

        def __default__(self, data, children, _):
            if data in self.as_list:
                return list(children)
            if data in self.to_obj:
                return self.to_obj[data](*children, meta=gen_meta(data))
            raise RuntimeError(f"Unknown rule {data}")
            #return Tree(data, children, meta)

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

        def hyperedge_definition(self, meta: Meta, name: VarOrParam, extends: Optional[Extends],
                                 loop: Optional[Loop], tags: list[str], param_block: list[Definition] = None,
                                 constraint_block: list[Constraint | CtrActivation] = None):
            constraint_block = constraint_block or []
            activations = [x for x in constraint_block if isinstance(x, CtrActivation)]
            constraint_block = [x for x in constraint_block if isinstance(x, Constraint)]
            param_block = param_block or []

            if loop is None:
                if len(name.path) != 1 or len(name.path[0].indices) != 0:
                    raise Exception(f"Invalid name for node: {name}")
                return HyperEdgeDefinition(name.path[0].name, extends, param_block, constraint_block,
                                           activations, tags, meta=meta)
            else:
                return HyperEdgeGenerator(name, loop, extends, param_block, constraint_block,
                                          activations, tags, meta=meta)

        def node_definition(self, meta: Meta, name: VarOrParam, extends: Optional[Extends],
                            loop: Optional[Loop], tags: list[str],
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
                if len(name.path) != 1 or len(name.path[0].indices) != 0:
                    raise Exception(f"Invalid name for node: {name}")
                return NodeDefinition(name.path[0].name, extends, param_block,
                                      subprogram_block.nodes, subprogram_block.hyperedges,
                                      variable_block, constraint_block,
                                      objectives_block, activations, tags, meta=meta)
            else:
                return NodeGenerator(name, loop, extends, param_block,
                                     subprogram_block.nodes, subprogram_block.hyperedges,
                                     variable_block, constraint_block,
                                     objectives_block, activations, tags, meta=meta)

        def node_import(self, meta: Meta, name: str, imported_name: VarOrParam, imported_from: str, redef: list[ScopeChange | Definition]):
            return NodeImport(name, imported_name, imported_from,
                              [x for x in redef if isinstance(x, ScopeChange)],
                              [x for x in redef if isinstance(x, Definition)], meta=meta)

        def start(self, meta: Meta, time_horizon: Optional[int], global_defs: list[Definition], nodes_hyperedges: NodesAndHyperEdges):
            return GBOMLGraph(time_horizon, global_defs, nodes_hyperedges.nodes, nodes_hyperedges.hyperedges, meta=meta)

        def variable_definition(self, meta: Meta, scope: VarScope, type: Optional[VarType], names: list[VarOrParam],
                                imports_from: Optional[list[VarOrParam]], tags: list[str]):
            if imports_from is not None and len(imports_from) != len(names):
                raise Exception("Invalid variable import, numbers of variables on the left and on the right-side of "
                                "`<-` don't match")
            for name, import_from in zip(names, imports_from or repeat(None, len(names))):
                yield VariableDefinition(scope, type or VarType.continuous, name, import_from, tags, meta=meta)

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

        def definition(self, meta: Meta, name: str, args: Optional[list[str]], typ: DefinitionType, val: RValue, tags: list[str]):
            if args is not None:
                if typ != DefinitionType.expression:
                    raise Exception("Functions can only be defined as expressions (use `<-` instead of `=`)")
                return FunctionDefinition(name, args, val, tags, meta=meta)
            elif typ == DefinitionType.expression:
                return ExpressionDefinition(name, val, tags, meta=meta)
            else:
                return ConstantDefinition(name, val, tags, meta=meta)

    return GBOMLLarkTransformer().transform(tree)