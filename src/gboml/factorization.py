from gboml.ast import *
from gboml.scope import ScopedVariableDefinition, get_scope_after_expr
from gboml.tools.tree_modifier import modify_hier
from dataclasses import replace
from typing import Optional, Any

def _process_var_in_gboml(elem: ExpressionDotCall|ExpressionArrayCall|PathRoot, hier: list[ExpressionOp|ExpressionArrayCall], indexed_vars_to_coefs: dict[tuple[str, Optional[Expression]], Expression], sign: int) -> None:
    """
    :param elem:
    :param hier:
    :param indexed_vars_to_coefs: {(var.path_to_str(), index_as_gboml_ast): coef_as_gboml_ast}
    :param sign: the sign of the coefficient to insert in (or update) indexed_vars_to_coefs (should be different between left handside and right handside of the (in)equation)
    :returns: 0, to remove the variable from the tree for the independant term calculation (and 0 since the expression should be linear)
    """
    if isinstance(elem, ExpressionArrayCall):
        return 0 if elem.lhs == 0 else elem

    if isinstance(scope := get_scope_after_expr(elem), ScopedVariableDefinition):
        coef = sign
        sign_has_changed = False
        var_idx = hier[-1].rhs if hier and isinstance(hier[-1], ExpressionArrayCall) and hier[-1].lhs is elem else 0
        for op in filter(lambda o: isinstance(o, ExpressionOp), reversed(hier)):
            op_new = replace(op, operands=tuple(operand for operand in op.operands if operand is not elem))
            if len(op_new.operands) != len(op.operands):
                match op.operator:
                    case Operator.plus:
                        pass
                    case Operator.minus:
                        if op.operands[0] is not elem:
                            sign_has_changed = not sign_has_changed
                    case Operator.unary_minus:
                        sign_has_changed = not sign_has_changed
                    case Operator.times:
                        coef = ExpressionOp(Operator.times, (coef, op_new.operands[0] if len(op_new.operands) == 1 else op_new))
                    case Operator.divide:
                        if op.operands[0] is not elem:
                            raise RuntimeError(f"Variable {scope.path_to_str()} is in the denominator, non-linear Constraint at {c.meta}.")
                        coef = ExpressionOp(Operator.divide, (coef, op_new.operands[0] if len(op_new.operands) == 1 else op_new))
                    case _:
                        raise RuntimeError(f"Unsupported ExpressionOp {op.operator} applied to {scope.path_to_str()}. Ensure that Constraint at {c.meta} is linear.")
            elem = op

        if sign_has_changed:
            coef = -coef if isinstance(coef, int) else ExpressionOp(Operator.unary_minus, (coef,))
        
        key = (scope.path_to_str(), var_idx)
        match indexed_vars_to_coefs.pop(key, None):
            case int(value) if value: coef = coef + value if isinstance(coef, int) else ExpressionOp(Operator.plus, (coef, value))
            case ExpressionOp(operator=Operator.plus, operands=operands): coef = ExpressionOp(Operator.plus, operands + (coef,))
            case ExpressionOp() as expr_op: coef = ExpressionOp(Operator.plus, (expr_op, coef))
        if coef:
            indexed_vars_to_coefs[key] = coef
        return 0
    return elem

def factorize_gboml(obj: StdConstraint|Objective, param_defs: dict[str, Any]) -> tuple[dict[tuple[str, Optional[Expression]], Expression], Expression]:
    """
    Factorize by group(variable.name, variable.index) and give their corresponding coef, as well as the independant term of the whole obj

    :param obj: a Standard Constraint or an Objective
    :param param_defs: a dictionary with key=ParameterDefinition.semantic.scope.path_to_str() and value is the already-evaluated value of GBOML ParameterDefinition
    :returns: tuple(indexed_vars_to_coefs, independant_term) - still in GBOML ast form - for a given Constraint   (see _process_var_in_gboml() for info about indexed_vars_to_coefs)
    """
    indexed_vars_to_coefs: dict[tuple[str, Optional[Expression]], Expression] = {}  # {(var.path_to_str(), index_as_gboml_ast): coef_as_gboml_ast}
    indep_term = 0
    if isinstance(obj, StdConstraint):
        lhs_indep = modify_hier(obj.lhs, {ExpressionOp, ExpressionArrayCall}, by_after=dict.fromkeys((ExpressionDotCall, ExpressionArrayCall, PathRoot), lambda elem,hier: _process_var_in_gboml(elem, hier, indexed_vars_to_coefs, +1)))
        rhs_indep = modify_hier(obj.rhs, {ExpressionOp, ExpressionArrayCall}, by_after=dict.fromkeys((ExpressionDotCall, ExpressionArrayCall, PathRoot), lambda elem,hier: _process_var_in_gboml(elem, hier, indexed_vars_to_coefs, -1)))
        indep_term = ExpressionOp(Operator.minus, (rhs_indep, lhs_indep))
    elif isinstance(obj, Objective):
        indep_term = modify_hier(obj.expression, {ExpressionOp, ExpressionArrayCall}, by_after=dict.fromkeys((ExpressionDotCall, ExpressionArrayCall, PathRoot), lambda elem,hier: _process_var_in_gboml(elem, hier, indexed_vars_to_coefs, +1)))

    return indexed_vars_to_coefs, indep_term
