from gboml.ast import *
from gboml.scope import *
from gboml.tools.tree_modifier import visit, visit_hier, modify_hier
from gboml.reserved_definitions import GBOML_RESERVED_DEFINITIONS

from graphlib import TopologicalSorter, CycleError
from typing import NamedTuple, Optional
import ast
import dataclasses
import numpy as np

def _add_dep(deps: dict[VarOrParamDefinition, set[VarOrParamDefinition]], hier: list[HierTypes], dep: Optional[Scope]) -> None:
    if dep is not None and isinstance(dep, VarOrParamDefScope) and (parent_def := get_parent_from_hier(hier, VarOrParamDefinition)) is not None:
        if parent_def in deps:
            deps[parent_def].add(dep.ast)
        else:
            deps[parent_def] = {dep.ast}


def _check_fct_use_and_def(elem: ExpressionDotCall|ExpressionFunctionCall|PathRoot, scope: Optional[Scope]) -> None:
    """ Compare function usage and definition """
    if not scope:
        return

    if isinstance(scope, ScopedFunctionDefinition) != isinstance(elem, ExpressionFunctionCall):
        raise RuntimeError(f"{elem} {elem.meta}: used as {'function' if isinstance(elem, ExpressionFunctionCall) else 'non-fonction'} "
                           f"but declared as {'function' if isinstance(scope, ScopedFunctionDefinition) else 'non-fonction'} {scope.ast.meta}!")
    elif isinstance(scope, ScopedFunctionDefinition) and isinstance(elem, ExpressionFunctionCall) and (
            not elem.operands or scope.ast not in GBOML_RESERVED_DEFINITIONS and all(not isinstance(arg, Loop) for arg in elem.operands) and len(elem.operands) != len(scope.ast.args)):
        raise RuntimeError(f"{elem} {elem.meta}: function call got {len(elem.operands)} arguments but declared with {len(scope.ast.args)} arguments at {scope.ast.meta}.")


def _check_var_or_param_scoping(elem: ExpressionDotCall|PathRoot, hier: list[HierTypes], deps: dict[VarOrParamDefinition, set[VarOrParamDefinition]]) -> None:
    """ Checks if elem is accessible in the current scope (if not, an error is raised), adds elem to its VarOrParamDefinition parent's dependencies """
    if isinstance(hier[-2], ExpressionFunctionCall|ExpressionDotCall) and hier[-2].lhs is elem:
        return

    scope = get_scope_after_expr(elem, get_scope_from_hier(hier))
    # a single PathRoot as array element, DictEntry value or ExpressionFunctionCall could be a function_call without argument (even if definition has 1+ arg)
    if not (isinstance(hier[-2], Array) and elem in hier[-2].content
            or isinstance(hier[-2], DictEntry) and elem is hier[-2].value
            or isinstance(hier[-2], ExpressionFunctionCall) and elem in hier[-2].operands):
        _check_fct_use_and_def(elem, scope)
    _add_dep(deps, hier, scope)


def _check_fct_scoping(elem: ExpressionFunctionCall, hier: list[HierTypes], deps: dict[VarOrParamDefinition, set[VarOrParamDefinition]]) -> None:
    _check_fct_use_and_def(elem, scope := get_scope_after_expr(elem, get_scope_from_hier(hier)))
    _add_dep(deps, hier, scope)


def _check_node_or_hyperedge_indices(elem: NodeDefinition|HyperEdgeDefinition, hier: list[HierTypes]) -> None:
    if not elem.indices:
        return
    scope = get_scope_from_hier(hier)
    for index in elem.indices:
        try:
            scope[index]
        except KeyError:
            raise KeyError(f"{elem} {elem.meta} index {index} can not be used in this scope")


def _topo_sort(globalScope: GlobalScope, deps) -> tuple[VarOrParamDefScope]:
    """ Performs the topological sort for VarOrParamDefinition elements (if there's a circular dependency, an error is raised), and returns the sorted elements (should be evaluated in the same order) """
    ts = TopologicalSorter()
    add_node = lambda definition: ts.add(definition, *deps.get(definition, frozenset()))
    visit(globalScope.ast, dict.fromkeys(VarOrParamDefinition.__args__, add_node))
    try:
        return tuple(ts.static_order())
    except CycleError as err:  # default error too long to print, so raise from None
        raise RuntimeError("Circular dependency found!", list(map(lambda dep: (dep.semantic.scope.path_to_str(), dep.meta), err.args[1]))) from None


def _evaluate_from_gboml(root: GBOMLObject, local_defs: dict[str, int|float], scope: Scope):
    return eval(compile(ast.fix_missing_locations(ast.Expression(to_python_ast(root, scope))), "", mode="eval"), None, local_defs)

def _process_constraint(c: Constraint, var_maps: dict[str, int], param_defs: dict[str, float], param_defs_and_zeroed_vars: dict[str, int|float], scope: Scope) -> None:
    """ Returns a tuple(variable_coefs, independant_term) for a given Constraint """
    new_line = [0] * len(var_maps)
    indep_term = 0
    def add_variable_in_constr(elem: ExpressionDotCall|PathRoot, hier: list[ExpressionOp], sign: int) -> None:
        """ Returns 0 (to remove the variable for the indep term calculation) and adds the var coef to the approriate index of new_line """
        if isinstance(scope_new := get_scope_after_expr(elem, scope), ScopedVariableDefinition):
            coef = sign
            sign_has_changed = False
            for op in reversed(hier):
                op_new = dataclasses.replace(op, operands=tuple(operand for operand in op.operands if operand is not elem))
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
                            # try:
                                # coef *= _evaluate_from_gboml(op_new, param_defs, scope)
                            # except NameError:
                                # raise RuntimeError(f"Non-linear Constraint at {c.meta} on variable {scope_new.path_to_str()}")
                        case Operator.divide:
                            if op.operands[0] is not elem:
                                raise RuntimeError(f"Variable {scope_new.path_to_str()} is in the denominator, non-linear Constraint at {c.meta}.")
                            coef = ExpressionOp(Operator.divide, (coef, op_new.operands[0] if len(op_new.operands) == 1 else op_new))
                            # try:
                                # coef /= _evaluate_from_gboml(op_new, param_defs, scope)
                            # except NameError:
                                # raise RuntimeError(f"Non-linear Constraint at {c.meta} on variable {scope_new.path_to_str()}")
                        case _:
                            raise RuntimeError(f"Unsupported ExpressionOp {op.operator} applied to {scope_new.path_to_str()}. Ensure that Constraint at {c.meta} is linear.")
                elem = op

            if sign_has_changed:
                coef = -coef if isinstance(coef, int) else ExpressionOp(Operator.unary_minus, (coef,))
            
            match new_line[idx := var_maps[scope_new.path_to_str()]]:
                case 0: new_line[idx] = coef
                case int(value): new_line[idx] = coef + value if isinstance(coef, int) else ExpressionOp(Operator.plus, (coef, value))
                case ExpressionOp(operator=Operator.plus, operands=operands) as expr_op: new_line[idx] = dataclasses.replace(expr_op, operands=operands + (coef,))
                case ExpressionOp() as expr_op: new_line[idx] = ExpressionOp(Operator.plus, (expr_op, coef))
            return 0
        return elem

    if isinstance(c, StdConstraint):
        lhs_indep = modify_hier(c.lhs, {ExpressionOp}, by_after=dict.fromkeys((ExpressionDotCall, PathRoot), lambda elem,hier: add_variable_in_constr(elem, hier, +1)))
        rhs_indep = modify_hier(c.rhs, {ExpressionOp}, by_after=dict.fromkeys((ExpressionDotCall, PathRoot), lambda elem,hier: add_variable_in_constr(elem, hier, -1)))
        indep_term = ExpressionOp(Operator.minus, (lhs_indep, rhs_indep))

    return new_line, indep_term



def semantic_check(tree: GBOMLGraph) -> None:
    # check if variables are in scope, and store deps
    deps: dict[VarOrParamDefinition, set[VarOrParamDefinition]] = {}
    visit_hier(tree, set(HierTypes.__args__), {ExpressionFunctionCall: lambda elem,hier: _check_fct_scoping(elem, hier, deps)} | dict.fromkeys((ExpressionDotCall, PathRoot), lambda elem,hier: _check_var_or_param_scoping(elem, hier, deps)) | dict.fromkeys((NodeDefinition, HyperEdgeDefinition), _check_node_or_hyperedge_indices))

    sorted_varorparam_defs = _topo_sort(tree.semantic.scope, deps)
    del deps
    print(sorted_varorparam_defs)
    param_defs = {}
    for d in filter(lambda x: isinstance(x, Definition), sorted_varorparam_defs):
        if isinstance(d, FunctionDefinition | FunctionConstraintDefinition):  # this is to skip global defs like len()
            continue
        param_defs[d.semantic.scope.path_to_str()] = eval(compile(ast.fix_missing_locations(ast.Expression(to_python_ast(d.value, d.semantic.scope))), "", mode="eval"), None, param_defs)
    print("all params values: ", param_defs, len(param_defs))

    var_maps = {}  # map all variables to a different index
    var_idx = 0
    def update_var_maps(var) -> None:
        nonlocal var_idx
        var_maps[var.semantic.scope.path_to_str()] = var_idx
        var_idx += 1
    visit(tree, {VariableDefinition: update_var_maps})
    del var_idx
    print("variables mapping idx: ", var_maps)
    param_defs_and_zeroed_vars = param_defs | dict.fromkeys(var_maps, 0)
    print("params with zero'd vars: ", param_defs_and_zeroed_vars)
    var_coefs: list[list[float]] = []
    indep_terms: list[float] = []
    def add_coefs_and_term(c: Constraint, hier: list[HierTypes]) -> None:
        coefs, term = _process_constraint(c, var_maps, param_defs, param_defs_and_zeroed_vars, get_scope_from_hier(hier))
        var_coefs.append(coefs)
        indep_terms.append(term)
    visit_hier(tree, set(HierTypes.__args__), {Constraint: add_coefs_and_term})
    print("matrices:\n", var_coefs, indep_terms)

# enregistrer pas direct (en évaluation) dans matrice mais symboliquement par variabble(et idx) différentes; car mieux pour générer des arrays pour les variables indiçantes si dans coef
# simplement partir de feuille si c'est une variable, remonter jusqu'à root en faisant les bonnes opérations (ne pas oublier: checker si linéaire). additionner les coef si plusieurs fois la variable avec GBOML.add
# pour terme indépendant, même chose (AST symbolique) en mettant tous les variables = 0

# A=( colonne=param ligne=contrainte) x=(vars) = b=(const part from constraints)

# factorisation: tuple (coefficient de variable, indice de variable possiblement None)
# gen: loop generateur (implicit et/ou explicite)
# sign: <= == >=
# terme indépendant

# pour faire la factorisation, faire un AST par variable; un AST par x[t+1] avec même nom de variable et même indice (symboliquement!) x[t] != x[t+0]

# TODO quand on évalue les indices faudrait-il enregistrer la conversion ASTGboml -> ASTPython?

# TODO use by_after for all modify/modify_hier when possible


# TODO list
#
# Add support for params importing a csv
#
# Should we forbid A.B.C.param ? C.B.A.param is always allowed because of parent.parent.parent.param
#
# I think modify() does not work if by_before AND by_after change the whole node
#
# a1 = 1(5); should not be accepted by Lark
#
# VarOrParam values propagation:
# DO NOT EVALUATE VALUES IF NOT USED (aka only evaluate the varorparams from objective/contraint expressions)
# using the list returned by the toposort, know which nodes don't do anything with iterable and propagate scalar value for these ones
# once done, do 2nd pass to check for all types (e.g. array declaration vs use (like _check_fct_use_and_def); cannot ExpressionFunctionCall on a STRING/Array/Dictionary, no allowed operation with STRING, ...)
# also, Activations should be processed (non-conditional ones are already processed by tree_post_process.py): the conditions should only contains params (no variables)
# make sure Activations are well done, lots of edge cases (e.g. if conditionnally deactivate an already deactivated constraint, should drop completely the conditionnally constraint)
#
# Can params use vars in their expression ? At least forbid it in GLOBAL and TIMEHOZIRON
#
# Allow TIMEHORIZON to use global variables (as it already can use node's params)
#
# Documentation in folder docs (for readthedocs.io)
# say that adding Function(Constraint) needs to be done in reserved_keywords.py; say that multine comment /* */ is supported
#
# Errors
# Should not stop at first error, and should be nicer print ('B.param', not ExpressionDotCall(lhs=PathRoot(name='B'), rhs='param')) by e.g. defining a short_string() in gboml.ast
# Can be implemented with function decorator or separate additionnal argument to all functions
#
# Production tests:
# - use pyright to check for correct typing of method etc
# - add test to check 'assert Operator("<") is Operator.lesser' and 'assert Operator("<") == Operator.lesser'
