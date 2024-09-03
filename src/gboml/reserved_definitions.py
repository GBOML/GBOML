from gboml.ast.variables import FunctionDefinition, IndexingParameterDefinition, ConstantDefinition
from gboml.ast.base import Meta
from gboml.ast.arrays import Range
from gboml.ast.path import PathRoot
from gboml.ast.expression_operators import ExpressionOp, Operator

_meta = Meta('$reserved_definitions.gboml$', -1, -1)
GBOML_RESERVED_DEFINITIONS = (
	FunctionDefinition('len', ('_',), None, meta=_meta),
	FunctionDefinition('sum', ('_',), None, meta=_meta),
	FunctionDefinition('SOS1', ('_',), None, meta=_meta),  # warning, can only be used as FunctionConstraint TODO check
	FunctionDefinition('SOS2', ('_',), None, meta=_meta),  # warning, can only be used as FunctionConstraint
	# warning, if adding FunctionConstraintDefinition, add them in parsing.py too
    IndexingParameterDefinition('t', Range(0, ExpressionOp(Operator.minus, operands=(PathRoot(name='T'), 1))), meta=_meta),
	ConstantDefinition('T', 0, meta=_meta)
)
