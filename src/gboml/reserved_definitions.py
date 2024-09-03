from gboml.ast.variables import FunctionDefinition, FunctionConstraintDefinition, IndexingParameterDefinition, ConstantDefinition
from gboml.ast.base import Meta
from gboml.ast.arrays import Range
from gboml.ast.path import PathRoot
from gboml.ast.expression_operators import ExpressionOp, Operator

_meta = Meta('$reserved_definitions.gboml$', -1, -1)
GBOML_RESERVED_DEFINITIONS = (
	FunctionDefinition('len', ('_',), None, meta=_meta),
	FunctionDefinition('sum', ('_',), None, meta=_meta),
	FunctionConstraintDefinition('SOS1', ('_',), None, meta=_meta),
	FunctionConstraintDefinition('SOS2', ('_',), None, meta=_meta),
    IndexingParameterDefinition('t', Range(0, ExpressionOp(Operator.minus, operands=(PathRoot(name='T'), 1))), meta=_meta),
	ConstantDefinition('T', 0, meta=_meta)
)
