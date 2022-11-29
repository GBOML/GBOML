import pathlib

from lark import Lark, Tree, Token, Transformer, v_args
from gboml.ast import *
from typing import Optional
from collections import namedtuple

parser = Lark(open((pathlib.Path(__file__).parent / "gboml.lark").resolve()).read(), start="start", parser="lalr")


def parse_file(filename: str) -> GBOMLGraph:
    """
    Args:
        filename: path to the GBOML-formatted text to parse
    Returns: a GBOMLGraph
    """
    return parse(open(filename).read(), filename)


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
            "objectives_block", "constraints_block", "variables_block",
            "parameters_block", "global_block", "plist", "node_redefs",
            "hyperedge_redefs", "separated_list", "array"
        }

        #
        # These rules will be converted to the given object, by calling
        # obj(*children, meta=meta)
        #
        to_obj = {
            "hyperedge_definition": HyperEdgeDefinition,
            "hyperedge_import": HyperEdgeImport,
            "definition": Definition,
            "var_or_param_leaf": VarOrParamLeaf,
            "var_or_param": VarOrParam,
            "constraint_std": StdConstraint,
            "constraint_sos": SOSConstraint,
            "objective": Objective,
            "full_loop": Loop,
            "implicit_loop": ImplicitLoop,
            "substraction": op_transform(Operator.minus),
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
            "generated_expression": GeneratedExpression,
            "import": Import,
            "variable_scope_change": ScopeChange
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
        def SCOPE(self, token): return VarScope(token.value)
        def SOS_TYPE(self, token): return SOSType(token.value)
        def CTR_OPERATOR(self, token): return Operator(token.value)
        def OBJ_TYPE(self, token): return ObjType(token.value)
        def COMPARISON_OPERATOR(self, token): return Operator(token.value)
        def STRING(self, token): return token.value[1:-1].replace('\\"', '"')
        def VTYPE(self, token): return VarType(token.value)

        NodesAndHyperEdges = namedtuple("NodesAndHyperEdges", ["nodes", "hyperedges"])

        def program_block(self, meta: Meta, *childrens: list[Node | HyperEdge]) -> NodesAndHyperEdges:
            return self.NodesAndHyperEdges([x for x in childrens if isinstance(x, Node)], [x for x in childrens if isinstance(x, HyperEdge)])

        def node_definition(self, meta: Meta, name: str, param_block: list[Definition], subprogram_block: NodesAndHyperEdges,
                            variable_block: list[VariableDefinition], constraint_block: list[Constraint],
                            objectives_block: list[Objective]):
            return NodeDefinition(name, param_block,
                                  subprogram_block.nodes, subprogram_block.hyperedges,
                                  variable_block, constraint_block,
                                  objectives_block, meta=meta)

        def node_import(self, meta: Meta, name: str, imported_name: VarOrParam, imported_from: str, redef: list[ScopeChange | Definition]):
            return NodeImport(name, imported_name, imported_from,
                              [x for x in redef if isinstance(x, ScopeChange)],
                              [x for x in redef if isinstance(x, Definition)], meta=meta)

        def start(self, meta: Meta, time_horizon: Optional[int], global_defs: list[Definition], nodes_hyperedges: NodesAndHyperEdges):
            return GBOMLGraph(time_horizon, global_defs, nodes_hyperedges.nodes, nodes_hyperedges.hyperedges, meta=meta)

        def variable_definition(self, meta: Meta, scope: VarScope, type: Optional[VarType], name: VarOrParam, import_from: Optional[VarOrParam]):
            return VariableDefinition(scope, type or VarType.continuous, name, import_from, meta=meta)

    return GBOMLLarkTransformer().transform(tree)
