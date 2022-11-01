# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).
import array

from gboml.compiler.utils import error_
from .objective import Objective
from .constraint import Constraint
from .expression import Expression
from .identifier import Identifier
import copy
import numpy as np
from scipy.sparse import coo_matrix  # type: ignore


class ByteArray:
    def __init__(self, length):
        self.array = np.ones(length, dtype=bool)

    def intersect_inplace(self, values):
        self.array = self.array & values

    def reset(self):
        self.array = np.ones(len(self.array), dtype=bool)


def __f_index2__(expr, all_index, name):
    max_length = len(name)
    is_in = np.array(((0 <= expr) & (expr < max_length)), dtype=bool)
    all_index.array = all_index.array & is_in
    expr = np.array(expr, dtype=int)

    if not is_in.all():
        return_value = np.array(name[np.clip(expr, 0, max_length - 1)], dtype=float)
    else:
        return_value = np.array(name[expr], dtype=float)

    return return_value


def __f_index__(expr, all_index, max_length):
    nan_cond = expr != np.nan
    condition = (0 <= expr) & (expr < max_length) & nan_cond
    all_index.array = all_index.array & condition
    expr[nan_cond] = 0
    expr = np.array(expr, dtype=int)
    return np.clip(expr, 0, max_length-1)


def is_index_dependant_expression(expression, index) -> bool:

    e_type = expression.get_type()
    children = expression.get_children()
    predicate: bool = False
    if e_type == 'literal':

        seed = expression.get_name()
        if type(seed) == Identifier:

            identifier = seed
            id_type = identifier.get_type()
            id_name = identifier.get_name()
            if id_type == "assign":

                predicate = is_index_dependant_expression(
                    identifier.get_expression(), index)
            if id_name in index:

                predicate = True

    else:

        for child in children:
            predicate_i = is_index_dependant_expression(child, index)
            if predicate_i:

                predicate = predicate_i
                break

    return predicate


class Factorize:

    def __init__(self, obj):

        self.name = None
        type_fact = "sum"
        if type(obj) == Constraint:

            type_fact = "constraint"
        if type(obj) == Objective:

            type_fact = "objective"
        self.type_fact = type_fact
        self.coef_var_tuples = []
        self.indep_expr = None
        self.index_list = []
        self.obj = obj
        self.children = []
        self.mult_expr = None
        self.extension = []
        self.variables = []
        self.line = obj.get_line()
        self.extension_type = ""
        self.sparse = None
        self.independent_terms = []

    def get_name(self):
        return self.name

    def get_line(self):

        return self.line

    def add_coef_var_tuples(self, coef_var):

        self.coef_var_tuples.append(coef_var)

    def get_extension(self):

        return self.extension

    def set_indep_expr(self, expr):

        self.indep_expr = expr
    
    def add_child(self, s):

        self.children.append(s)

    def get_children(self):

        return self.children

    def get_indep_expr(self):

        return self.indep_expr

    def factorize(self, variables, constants, indexes):

        if self.type_fact == "constraint":

            return self.factorize_constraint(variables, constants)
        elif self.type_fact == "objective":

            return self.factorize_objective(variables, constants)
        else:

            return self.factorize_sum(variables, constants, indexes)

    def free(self):
        for child in self.children:
            child.coef_var_tuples = None
            child.obj = None

        self.children = None
        self.coef_var_tuples = None

    def factorize_constraint(self, variables, constants):

        constraint = self.obj
        self.name = constraint.name
        leaves_rhs = constraint.get_rhs().get_leafs()
        leaves_lhs = constraint.get_lhs().get_leafs()
        index_name = constraint.get_index_var() 
        self.index_list.append(index_name)
        var_leaves = []
        term_rhs, _ = self.compute_independant_term(constraint.get_rhs(),
                                                    variables)
        term_lhs, _ = self.compute_independant_term(constraint.get_lhs(),
                                                    variables)
        indep_term = Expression("-")
        indep_term.add_child(term_rhs)
        indep_term.add_child(term_lhs)
        self.set_indep_expr(indep_term)
        for leaf in leaves_rhs:

            inner_expr = leaf.get_name()
            l_type = leaf.get_type()
            if type(inner_expr) == Identifier:

                identifier: Identifier = inner_expr
                identifier_name = identifier.get_name()
                identifier_node_name = identifier.get_node_name()
                if identifier_node_name in variables and \
                        identifier_name in variables[identifier_node_name]:

                    var = variables[identifier_node_name][identifier_name]
                    identifier_var = var.get_identifier()
                    var_leaves.append([-1, leaf, identifier,
                                       identifier_var.get_index(),
                                       identifier_var.get_size()])
                    self.variables.append([identifier_node_name,
                                           identifier_name])

            elif l_type == "sum":
                fct_constr = Factorize(leaf)
                is_var = fct_constr.factorize_sum(variables, constants,
                                                  self.index_list)
                if is_var is True:
                    self.add_child([-1, fct_constr])
                self.variables += fct_constr.variables

        for leaf in leaves_lhs:

            inner_expr = leaf.get_name()
            l_type = leaf.get_type()
            if type(inner_expr) == Identifier:

                identifier: Identifier = inner_expr
                identifier_name = identifier.get_name()
                identifier_node_name = identifier.get_node_name()
                if identifier_node_name in variables and \
                        identifier_name in variables[identifier_node_name]:
                    var = variables[identifier_node_name][identifier_name]
                    identifier_var = var.get_identifier()
                    var_leaves.append([1, leaf, identifier,
                                       identifier_var.get_index(),
                                       identifier_var.get_size()])
                    self.variables.append([identifier_node_name,
                                           identifier_name])
            elif l_type == "sum":

                fct_constr = Factorize(leaf)
                is_var = fct_constr.factorize_sum(variables, constants,
                                                  self.index_list)
                if is_var is True:

                    self.add_child([1, fct_constr])
                    self.variables += fct_constr.variables
        coef_var = []
        for rhs_bool, leaf, identifier, index, var_size in var_leaves:

            parent = leaf.get_parent()
            expr = Expression('literal', 1, line=leaf.get_line())
            expr_coef, _ = self.compute_factor(expr, False, parent,
                                               leaf, constants)
            expr = identifier.get_expression()
            coef_var.append([rhs_bool, expr_coef, index, expr, var_size])
        self.coef_var_tuples = coef_var

    def factorize_objective(self, variables, constants):

        objective = self.obj
        self.name = objective.name
        obj_expr = objective.get_expression()
        leaves = obj_expr.get_leafs()
        index_name = objective.get_index_var() 
        self.index_list.append(index_name)
        term_indep, _ = self.compute_independant_term(obj_expr, variables)
        self.set_indep_expr(term_indep)
        var_leaves = []
        for leaf in leaves:

            inner_expr = leaf.get_name()
            l_type = leaf.get_type()
            if type(inner_expr) == Identifier:

                identifier: Identifier = inner_expr
                identifier_node_name = identifier.get_node_name()
                identifier_name = identifier.get_name()
                if identifier_node_name in variables \
                        and identifier_name in variables[identifier_node_name]:

                    var = variables[identifier_node_name][identifier_name]
                    var_identifier = var.get_identifier()
                    var_leaves.append([leaf, var_identifier.get_index(),
                                       var_identifier.get_size()])
            if l_type == "sum":

                fct_constr = Factorize(leaf)
                is_var = fct_constr.factorize_sum(variables, constants,
                                                  self.index_list)
                if is_var is True:

                    self.add_child(fct_constr)
        coef_var = []
        for leaf, index, var_size in var_leaves:

            parent = leaf.get_parent()
            expr = Expression('literal', 1, line=leaf.get_line())
            expr_coef, _ = self.compute_factor(expr, False, parent, leaf,
                                               constants)
            identifier = leaf.get_name()
            expr = identifier.get_expression()
            coef_var.append([expr_coef, index, expr, var_size])
        self.coef_var_tuples = coef_var

    def factorize_sum(self, variables, constants, indexes):

        expression_sum = self.obj
        is_var = False
        var_leaves = []
        children = expression_sum.get_children()
        leaves = children[0].get_leafs()
        time_interval = expression_sum.get_time_interval()
        name_index = time_interval.get_index_name()
        self.index_list = indexes
        self.index_list.append(name_index)
        for leaf in leaves:

            inner_expr = leaf.get_name()
            l_type = leaf.get_type()
            if type(inner_expr) == Identifier:

                identifier: Identifier = inner_expr
                identifier_node_name = identifier.get_node_name()
                identifier_name = identifier.get_name()
                if identifier_node_name in variables and \
                        identifier_name in variables[identifier_node_name]:

                    var = variables[identifier_node_name][identifier_name]
                    variable_identifier = var.get_identifier()
                    var_leaves.append([leaf, variable_identifier.get_index(),
                                       variable_identifier.get_size()])
                    is_var = True
                    self.variables.append([identifier_node_name,
                                           identifier_name])
            if l_type == "sum":

                fct_constr = Factorize(leaf)
                is_var_sum = fct_constr.factorize_sum(variables,
                                                      constants, self.index_list)
                if is_var_sum is True:

                    self.add_child(fct_constr)
                    is_var = True
                    self.variables += fct_constr.variables
        expr = Expression('literal', 1, line=expression_sum.get_line())
        parent = expression_sum.get_parent()
        expr_coef, _ = self.compute_factor(expr, False, parent,
                                           expression_sum, constants)
        self.mult_expr = expr_coef
        coef_var = []
        for leaf, index, var_size in var_leaves:

            parent = leaf.get_parent()
            expr = Expression('literal', 1, line=leaf.get_line())
            expr_coef, _ = self.compute_factor(expr, False, parent,
                                               leaf, constants,
                                               stop_expr=expression_sum)
            identifier = leaf.get_name()
            expr = identifier.get_expression()

            coef_var.append([expr_coef, index, expr, var_size])
        self.coef_var_tuples = coef_var

        return is_var

    def compute_independant_term(self, expr, variables):
        
        children = expr.get_children()
        expr_type = expr.get_type()
        is_var = False
        expr_acc = Expression("literal", 0)
        if expr_type == "literal":

            seed = expr.get_name()
            if type(seed) == float or type(seed) == int:

                expr_acc = copy.copy(expr)
            elif type(seed) == Identifier:

                identifier: Identifier = seed
                identifier_name = identifier.get_name()
                identifier_node_name = identifier.get_node_name()
                if identifier_node_name in variables \
                        and identifier_name in variables[identifier_node_name]:

                    is_var = True
                else:

                    expr_acc = copy.copy(expr)

        else:

            tuple_expr_is_var = []
            for child in children:

                expr_child, is_var_child = \
                    self.compute_independant_term(child, variables)
                tuple_expr_is_var.append([expr_child, is_var_child])
            if expr_type in ["*", "/", "**", "mod"]:

                expr1, var_1 = tuple_expr_is_var[0]
                expr2, var_2 = tuple_expr_is_var[1]
                if var_1 or var_2:

                    is_var = True
                else:

                    expr_acc = Expression(expr_type)
                    expr_acc.add_child(expr1)
                    expr_acc.add_child(expr2)

            elif expr_type == "u-":

                expr1, is_var = tuple_expr_is_var[0]
                if is_var is False:

                    expr_acc = Expression("u-")
                    expr_acc.add_child(expr1)
                else:

                    expr_acc = expr1
            elif expr_type in ["+", "-"]:

                expr1, var_1 = tuple_expr_is_var[0]
                expr2, var_2 = tuple_expr_is_var[1]
                if var_1 and var_2:

                    is_var = True
                elif var_1 is False and var_2 is False:

                    expr_acc = Expression(expr_type)
                    expr_acc.add_child(expr1)
                    expr_acc.add_child(expr2)
                elif var_1 is False:

                    expr_acc = expr1
                elif var_2 is False:

                    if expr_type == "-":

                        expr_acc = Expression("u-")
                        expr_acc.add_child(expr2)
                    else:

                        expr_acc = expr2
            elif expr_type == "sum":

                expr1, var_1 = tuple_expr_is_var[0]
                if var_1:

                    is_var = True
                else:

                    time_interval = expr.get_time_interval()
                    expr_acc = Expression('sum')
                    expr_acc.add_child(expr1)
                    expr_acc.set_time_interval(time_interval)

        return expr_acc, is_var

    def compute_factor(self, expr_acc, is_index_dependant, parent_expr,
                       branch_considered, constants, stop_expr=None):
        
        if parent_expr is None or parent_expr == stop_expr or \
                (self.type_fact == "sum" and parent_expr.get_type() == "sum"):

            return expr_acc, is_index_dependant
        children = parent_expr.get_children()
        other_children = []
        p_type = parent_expr.get_type()
        if p_type == "*" or p_type == "/":
            
            i = 0
            for child in children:

                if child != branch_considered:

                    other_children.append((child, i))
                i = i+1
            child, position = other_children[0]
            other_child_time_dependancy = \
                is_index_dependant_expression(child, self.index_list)
            if other_child_time_dependancy is False:

                term1 = child.evaluate_expression(constants)
                if is_index_dependant is False:

                    term2 = expr_acc.evaluate_expression(constants)
                    value = 0
                    if p_type == '*':

                        value = term1 * term2
                    elif p_type == '/':

                        if position == 0:

                            value = term1/term2
                        else:

                            value = term2/term1
                    expr_acc = Expression("literal", value)
                else:

                    copy_child = Expression("literal", term1)
                    expr = Expression(p_type)
                    expr.add_child(expr_acc)
                    expr.add_child(copy_child)
                    expr_acc = expr
            else:

                is_index_dependant = other_child_time_dependancy
                copy_child = copy.copy(child)
                expr = Expression(p_type)
                expr.add_child(expr_acc)
                expr.add_child(copy_child)
                expr_acc = expr
        elif p_type == "-":

            i = 0
            position = 0
            for child in children:

                if child == branch_considered:

                    position = i
                i = i+1
            
            if position == 1:

                if is_index_dependant is False:

                    value = expr_acc.evaluate_expression(constants)
                    expr_acc = Expression("literal", -value)
                else:

                    expr = Expression('u-')
                    expr.add_child(expr_acc)
                    expr_acc = expr
        elif p_type == "u-":

            if is_index_dependant is False:

                value = expr_acc.evaluate_expression(constants)
                expr_acc = Expression("literal", -value)
            else:

                expr = Expression('u-')
                expr.add_child(expr_acc)
                expr_acc = expr
        branch_considered = parent_expr
        parent_expr = parent_expr.get_parent()
        
        return self.compute_factor(expr_acc, is_index_dependant, parent_expr,
                                   branch_considered, constants, stop_expr)

    def extend(self, definitions, list_indexes=None):
        if list_indexes is None:
            list_indexes = []
        time_horizon = definitions["T"]
        coef_var_tuples = self.coef_var_tuples
        new_coef_var_tuples = []
        for elements in coef_var_tuples:
            list_elements = []
            for element in elements:
                if isinstance(element, Expression):
                    element = element.turn_to_python_expression()
                list_elements.append(element)
            new_coef_var_tuples.append(list_elements)
        coef_var_tuples = new_coef_var_tuples
        nb_coef_var = len(coef_var_tuples)
        explicit_time_range = False
        children_sums = self.get_children()
        list_values_columns = []
        gl = {"sum": sum, "range": range, "len": len,
              "__f_index__": __f_index2__}
        if self.type_fact != "sum":
            gl.update(definitions)
        if self.type_fact == "constraint":
            constraint = self.obj
            b_expr = self.get_indep_expr().turn_to_python_expression()
            sign = constraint.get_sign()
            self.extension_type = sign
            time_range = constraint.get_time_range(gl)
            name_index = constraint.get_index_var()
            condition = constraint.get_condition()
            all_values = []
            all_columns = []
            if condition is not None:
                condition_expression = condition.turn_to_python_expression()
            else:
                condition_expression = True

            if time_range is None:
                if (not is_index_dependant_expression(constraint.get_rhs(),
                                                      name_index)) and \
                        (not is_index_dependant_expression(constraint.get_lhs(),
                                                           name_index)):
                    if condition is None:
                        t_horizon = 1
                    elif not is_index_dependant_expression(condition, name_index):
                        t_horizon = 1
                    else:
                        t_horizon = time_horizon
                else:
                    t_horizon = time_horizon

                time_range = range(t_horizon)
            else:
                explicit_time_range = True
            numpy_range = np.array(time_range)
            gl[name_index] = numpy_range
            if condition is not None:
                cond_eval = None
                try:
                    cond_eval = eval(condition_expression, gl, {})
                except IndexError:
                    error_("ERROR: error while evaluating the condition at line %s"
                           % (str(constraint.get_line())))
                time_range = [time_i for time_i, cond_i in list(zip(time_range, cond_eval)) if cond_i]
            bit_array = ByteArray(len(time_range))
            numpy_range = np.array(time_range)
            gl[name_index] = numpy_range
            gl["extension_range"] = bit_array
            for mult_sign, expr_coef, index, offset_expr, max_size \
                    in coef_var_tuples:
                coef_values = mult_sign * eval(expr_coef, gl, {})
                if offset_expr is not None:
                    offset = eval(offset_expr, gl, {})
                    offset = np.array(offset, dtype=int)
                else:
                    offset = 0
                bit_array.intersect_inplace((0 <= offset) & (offset < max_size))
                if not bit_array.array.any() and explicit_time_range:
                    error_("Constraint : " + str(constraint)
                           + " at line " + str(constraint.get_line())
                           + " has a time range ill-defined as a "
                             "variable goes out of bounds for "
                           + str(name_index) + " equals " + str(numpy_range[not bit_array.array]))
                all_values.append(coef_values)
                all_columns.append(offset + index)
            previous_child_values = np.array([[]])
            previous_child_columns = np.array([[]])
            i = 0
            child_bool = False
            if children_sums:
                child_bool = True

            for sign_mult, child in children_sums:
                child.extend(gl, list_indexes=[name_index])
                child_val, child_col = child.get_extension()
                child_val = sign_mult*child_val
                if i == 0:
                    previous_child_values = child_val
                    previous_child_columns = child_col
                else:
                    previous_child_columns = np.concatenate((previous_child_columns, child_col), axis=1)
                    previous_child_values = np.concatenate((previous_child_values, child_val), axis=1)
                i = i + 1

            if b_expr is not None:
                constant = eval(b_expr, gl, {})
            else:
                constant = 0
            valid_indexes = numpy_range[bit_array.array]
            _, child_nb_col = previous_child_columns.shape
            nb_valid_indexes = len(valid_indexes)
            values_flat_array = np.zeros(nb_valid_indexes * (nb_coef_var + child_nb_col))
            columns_flat_array = np.zeros(nb_valid_indexes * (nb_coef_var + child_nb_col))
            row_flat_array = np.arange(nb_valid_indexes)
            row_flat_array = np.repeat(row_flat_array, (nb_coef_var + child_nb_col))

            if isinstance(constant, np.ndarray):
                independent_term = np.array(constant[bit_array.array], dtype=float)
            else:
                independent_term = np.full(nb_valid_indexes, constant, dtype=float)
            for i in range(nb_coef_var):
                value_expr = all_values[i]
                column_expr = all_columns[i]
                if isinstance(value_expr, np.ndarray):
                    value_expr_right_index = value_expr[bit_array.array]
                    for j in range(len(valid_indexes)):
                        values_flat_array[j * (nb_coef_var + child_nb_col) + i] = value_expr_right_index[j]
                else:
                    for j in range(len(valid_indexes)):
                        values_flat_array[j * (nb_coef_var + child_nb_col) + i] = value_expr

                if isinstance(column_expr, np.ndarray):
                    column_expr_right_index = column_expr[bit_array.array]
                    for j in range(len(valid_indexes)):
                        columns_flat_array[j * (nb_coef_var + child_nb_col) + i] = column_expr_right_index[j]
                else:
                    for j in range(len(valid_indexes)):
                        columns_flat_array[j * (nb_coef_var + child_nb_col) + i] = column_expr

            if child_bool:
                value_expr_child_right_index = previous_child_values[bit_array.array]
                col_expr_child_right_index = previous_child_columns[bit_array.array]
                for j in range(len(valid_indexes)):
                    start_index_value = j * (nb_coef_var + child_nb_col) + nb_coef_var
                    end_index_value = j * (nb_coef_var + child_nb_col) + nb_coef_var + child_nb_col
                    values_flat_array[start_index_value:end_index_value] = value_expr_child_right_index[j]
                    columns_flat_array[start_index_value:end_index_value] = col_expr_child_right_index[j]

            if not bit_array.array.any():
                print("Warning constraint : %s at line %s is ignored for %s equal to %s"
                      % (str(constraint), str(constraint.get_line()), str(name_index),
                         str(numpy_range[not bit_array.array])))

            if nb_valid_indexes == 0:
                self.sparse = None
            else:
                #if self.obj.get_type() == "==":
                #    nb_values = len(values_flat_array)
                #    values_flat_array = np.tile(values_flat_array, 2)
                #    values_flat_array[nb_values:] = -values_flat_array[nb_values:]
                #    columns_flat_array = np.tile(columns_flat_array, 2)
                #   row_flat_array = np.tile(row_flat_array, 2)
                #   row_flat_array[nb_values:] = row_flat_array[nb_values:] + np.max(row_flat_array) + 1
                #   nb_valid_indexes = nb_valid_indexes*2
                #   nb_indep_values = len(independent_term)
                #   independent_term = np.tile(independent_term, 2)
                #   independent_term[nb_indep_values:] = -independent_term[nb_indep_values:]

                self.independent_terms = independent_term
                self.sparse = coo_matrix((values_flat_array, (row_flat_array, columns_flat_array)),
                                         shape=(nb_valid_indexes,
                                                int(np.max(columns_flat_array)) + 1))
                self.sparse.sum_duplicates()
                self.sparse.eliminate_zeros()

        elif self.type_fact == "objective":
            objective = self.obj
            obj_expr = objective.get_expression()
            obj_range = objective.get_time_range(definitions)
            name_index = objective.get_index_var()
            obj_type = objective.get_type()
            self.extension_type = obj_type
            b_expr = self.get_indep_expr().turn_to_python_expression()
            condition = objective.get_condition()
            if condition is not None:
                obj_condition = condition.turn_to_python_expression()
            else:
                obj_condition = True

            if obj_range is None:
                if (not is_index_dependant_expression(obj_expr,
                                                      name_index)):
                    t_horizon = 1
                else:
                    t_horizon = time_horizon
                obj_range = range(t_horizon)
            else:
                explicit_time_range = True
            numpy_range = np.array(obj_range)
            gl[name_index] = numpy_range

            if condition is not None:
                cond_eval = None
                try:
                    cond_eval = eval(obj_condition, gl, {})
                except IndexError:
                    error_("ERROR: error while evaluating the condition at line %s"
                           % (str(objective.get_line())))
                obj_range = [time_i for time_i, cond_i in list(zip(obj_range, cond_eval)) if cond_i]

            bit_array = ByteArray(len(obj_range))
            numpy_range = np.array(obj_range)
            gl[name_index] = numpy_range
            gl["extension_range"] = bit_array
            all_values = []
            all_columns = []
            for expr_coef, index, offset_expr, max_size in coef_var_tuples:
                coef_values = eval(expr_coef, gl, {})
                if offset_expr is not None:
                    offset = eval(offset_expr, gl, {})
                else:
                    offset = 0
                bit_array.intersect_inplace((0 <= offset) & (offset < max_size))
                if not bit_array.array.any() and explicit_time_range:
                    error_("Constraint : " + str(objective)
                           + " at line " + str(objective.get_line())
                           + " has a time range ill-defined as a "
                             "variable goes out of bounds for "
                           + str(name_index) + " equals " + str(numpy_range[not bit_array.array]))
                all_values.append(coef_values)
                all_columns.append(offset + index)
            previous_child_values = np.array([[]])
            previous_child_columns = np.array([[]])
            i = 0
            child_bool = False
            if children_sums:
                child_bool = True
            for child in children_sums:
                child.extend(gl, list_indexes=[name_index])
                child_val, child_col = child.get_extension()
                if i == 0:
                    previous_child_values = child_val
                    previous_child_columns = child_col
                else:
                    previous_child_columns = np.concatenate((previous_child_columns, child_col), axis=1)
                    previous_child_values = np.concatenate((previous_child_values, child_val), axis=1)
                i = i + 1
            if b_expr is not None:
                constant = eval(b_expr, gl, {})
            else:
                constant = 0
            valid_indexes = numpy_range[bit_array.array]
            _, child_nb_col = previous_child_columns.shape
            nb_valid_indexes = len(valid_indexes)
            values_flat_array = np.zeros(nb_valid_indexes * (nb_coef_var + child_nb_col))
            columns_flat_array = np.zeros(nb_valid_indexes * (nb_coef_var + child_nb_col))
            row_flat_array = np.arange(nb_valid_indexes)
            row_flat_array = np.repeat(row_flat_array, (nb_coef_var + child_nb_col))
            if isinstance(constant, np.ndarray):
                independent_term = np.array(constant[valid_indexes], dtype=float)
            else:
                independent_term = np.full(nb_valid_indexes, constant, dtype=float)
            for i in range(nb_coef_var):
                value_expr = all_values[i]
                column_expr = all_columns[i]
                if isinstance(value_expr, np.ndarray):
                    value_expr_right_index = value_expr[bit_array.array]
                    for j in range(len(valid_indexes)):
                        values_flat_array[j * (nb_coef_var + child_nb_col) + i] = value_expr_right_index[j]
                else:
                    for j in range(len(valid_indexes)):
                        values_flat_array[j * (nb_coef_var + child_nb_col) + i] = value_expr

                if isinstance(column_expr, np.ndarray):
                    column_expr_right_index = column_expr[bit_array.array]
                    for j in range(len(valid_indexes)):
                        columns_flat_array[j * (nb_coef_var + child_nb_col) + i] = column_expr_right_index[j]
                else:
                    for j in range(len(valid_indexes)):
                        columns_flat_array[j * (nb_coef_var + child_nb_col) + i] = column_expr

            if child_bool:
                value_expr_child_right_index = previous_child_values[bit_array.array]
                col_expr_child_right_index = previous_child_columns[bit_array.array]
                for j in range(len(valid_indexes)):
                    start_index_value = j * (nb_coef_var + child_nb_col) + nb_coef_var
                    end_index_value = j * (nb_coef_var + child_nb_col) + nb_coef_var + child_nb_col
                    values_flat_array[start_index_value:end_index_value] = value_expr_child_right_index[j]
                    columns_flat_array[start_index_value:end_index_value] = col_expr_child_right_index[j]

            if not bit_array.array.any():
                print("Warning constraint : %s at line %s is ignored for %s equal to %s"
                      % (str(objective), str(objective.get_line()), str(name_index),
                         str(numpy_range[not bit_array.array])))

            if nb_valid_indexes == 0 or len(values_flat_array) == 0:
                self.sparse = None
                self.independent_terms = np.array(independent_term,
                                                  dtype=float)
            else:

                rows = row_flat_array
                columns = columns_flat_array
                values = values_flat_array

                self.independent_terms = np.array(independent_term,
                                                  dtype=float)
                self.sparse = coo_matrix((values, (rows, columns)),
                                         shape=(int(np.max(rows))+1,
                                                int(np.max(columns))+1))
                self.sparse.sum_duplicates()
                self.sparse.eliminate_zeros()

        elif self.type_fact == "sum":
            expr_sum = self.obj
            time_interval = expr_sum.get_time_interval()
            name_index = time_interval.get_index_name()
            range_index = time_interval.get_range(definitions, list_indexes=list_indexes)
            nan_vector = np.isnan(range_index)
            range_index[nan_vector] = 0
            not_nan_vector = np.bitwise_not(nan_vector)
            # nan_bool = nan_vector.any()
            nb_lines, nb_col = range_index.shape
            condition = expr_sum.get_condition()
            range_index = range_index.flatten()
            definitions[name_index] = range_index

            if condition is not None:
                obj_condition = condition.turn_to_python_expression()
            else:
                obj_condition = True

            if condition is not None:
                cond_eval = None
                try:
                    cond_eval = eval(obj_condition, definitions, {})
                except IndexError:
                    error_("ERROR: error while evaluating the condition at line %s"
                           % (str(expr_sum.get_line())))
                cond_eval = cond_eval.reshape(nb_lines, nb_col)
                not_nan_vector = cond_eval & not_nan_vector
                cond_eval = cond_eval & not_nan_vector
                nb_true_cond_eval = not_nan_vector.sum(axis=1)
                max_nb_true = max(nb_true_cond_eval)
                for i in range(nb_lines):
                    if nb_true_cond_eval[i] < max_nb_true:
                        nb_to_add = max_nb_true - nb_true_cond_eval[i]
                        for j in range(nb_col):
                            if cond_eval[i][j] == False:
                                cond_eval[i][j] = True
                                nb_to_add -= 1
                            if nb_to_add == 0:
                                break
                nb_col = max_nb_true
                not_nan_vector = not_nan_vector[cond_eval].reshape((nb_lines, nb_col))
                cond_eval = cond_eval.flatten()
                range_index = range_index[cond_eval.flatten()]
                definitions[name_index] = range_index
                nan_vector = np.bitwise_not(not_nan_vector)

            previous_values_dict = dict()
            multiplicator = eval(self.mult_expr.turn_to_python_expression(), definitions, {})
            if isinstance(multiplicator, np.ndarray):
                multiplicator = multiplicator.reshape(1, -1)

            for i in list_indexes:
                val = definitions[i]
                previous_values_dict[i] = val
                definitions[i] = np.repeat(definitions[i], nb_col)

            # definitions[name_index] = np.tile(range_index, repetition_length)
            bit_array = definitions["extension_range"]
            bit_array.array = np.repeat(bit_array.array, nb_col)
            all_values = []
            all_columns = []
            for expr_coef, index, offset_expr, max_size in coef_var_tuples:
                coef_values = eval(expr_coef, definitions, {})
                if offset_expr is not None:
                    offset = eval(offset_expr, definitions, {})
                else:
                    offset = 0
                bit_array.intersect_inplace((0 <= offset) & (offset < max_size))
                if not bit_array.array.any():
                    error_("Out of bounds sum at line "
                           + str(expr_sum.get_line()))
                all_values.append(coef_values)
                all_columns.append(offset+index)
            previous_column = np.array([]*nb_lines)
            previous_value = np.array([]*nb_lines)
            for i in range(nb_coef_var):

                current_value = all_values[i]
                if isinstance(current_value, np.ndarray):
                    current_value = np.reshape(current_value, (nb_lines, nb_col))
                    current_value[nan_vector] = 0
                else:
                    fill_value = current_value
                    current_value = np.zeros((nb_lines, nb_col))
                    current_value.fill(fill_value)
                    current_value[nan_vector] = 0

                current_column = all_columns[i]
                if isinstance(current_column, np.ndarray):
                    current_column = np.reshape(current_column, (nb_lines, nb_col))
                else:
                    fill_value = current_column
                    current_column = np.zeros((1, nb_lines))
                    current_column.fill(fill_value)
                    current_value = np.reshape(current_value.sum(axis=1), (1, -1))

                if i == 0:
                    previous_column = current_column
                    previous_value = current_value
                else:
                    previous_value = np.concatenate((previous_value, current_value), axis=1)
                    previous_column = np.concatenate((previous_column, current_column), axis=1)
            flatten_nan_vector = nan_vector.flatten()
            for child in children_sums:
                list_indexes.append(name_index)
                child.extend(definitions, list_indexes=list_indexes)
                tuple_val_col = child.get_extension()
                if not tuple_val_col:
                    error_("Out of bounds sum at line "
                           + str(expr_sum.get_line()))
                val_child, col_child = tuple_val_col
                val_child[flatten_nan_vector][:] = 0
                val_child = val_child.reshape(nb_lines, -1)
                col_child = col_child.reshape(nb_lines, -1)
                if previous_value:
                    previous_value = np.concatenate((previous_value, val_child), axis=1)
                    previous_column = np.concatenate((previous_column, col_child), axis=1)
                else:
                    previous_value = val_child
                    previous_column = col_child
                list_indexes.pop(-1)
            for i in list_indexes:
                definitions[i] = previous_values_dict[i]
            if name_index in definitions:
                del definitions[name_index]
            bit_array.array = np.reshape(bit_array.array,
                                         (nb_lines, nb_col))
            current_bit_array = bit_array.array
            bit_array.array[nan_vector] = True
            current_bit_array[nan_vector] = False
            bit_array.array = bit_array.array.all(axis=1)
            current_bit_array = current_bit_array.all(axis=1)
            values = np.reshape(previous_value, (nb_lines, -1))
            if isinstance(multiplicator, np.ndarray):
                values = np.multiply(values, multiplicator.T)
            else:
                values = multiplicator * values
            columns = np.reshape(previous_column, (nb_lines, -1))

            if not current_bit_array.any():
                error_("Error: No index in sum at line " + str(expr_sum.get_line()) + " works")
            list_values_columns = [values, columns]
        self.extension = list_values_columns
