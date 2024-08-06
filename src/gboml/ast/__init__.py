__all__ = [
    "Meta", "GBOMLObject", "VarScope", "VarType", "ObjType",
    "Operator", "ExpressionObj", "Expression", "Array", "Loop", "BaseLoop", "LikeLoop",
    "GeneratedObjectsType", "GeneratedObjects", "ImplicitLoop", "BoolExpressionOp", "BoolExpressionComparison",
    "ScopeChange", "ImportFile", "Definition", "Constraint", "StdConstraint", "FunctionConstraint",
    "Objective", "VariableDefinition", "NodeDefinition", "HyperEdgeDefinition",
    "ExpressionFunctionCall", "ExpressionOp", "GBOMLGraph", "VarOrParamDefinition",
    "Range", "DictEntry", "Dictionary", "NamedGBOMLObject", "Semantic",
    "DefinitionType", "FunctionDefinition", "ConstantDefinition", "ExpressionDefinition",
    "CtrActivation", "ObjActivation", "ActivationType", "Activation", "Extends", "Import",
    "AnyGBOMLObject", "IndexingParameterDefinition", "PossiblyGeneratedExpression",
    "ExpressionDotCall", "ExpressionArrayCall", "GeneratedExpression", "PathRoot", "Path"
]

from gboml.ast.activation import *
from gboml.ast.arrays import *
from gboml.ast.base import *
from gboml.ast.constraints import *
from gboml.ast.expression_operators import *
from gboml.ast.expressions import *
from gboml.ast.graph import *
from gboml.ast.hyperedges import *
from gboml.ast.import_file import *
from gboml.ast.importable import *
from gboml.ast.loops import *
from gboml.ast.nodes import *
from gboml.ast.objectives import *
from gboml.ast.path import *
from gboml.ast.values import *
from gboml.ast.variables import *

# TODO mark these attributes as Loop in classes using them
GeneratedObjectsType = NodeDefinition | HyperEdgeDefinition | GeneratedExpression | DictEntry | StdConstraint | Objective
GeneratedObjects = frozenset(GeneratedObjectsType.__args__)

VarOrParamDefinition = Definition | VariableDefinition
