from compiler.utils import error_
from compiler.classes.objective import Objective
from compiler.classes.constraint import Constraint
from compiler.classes.expression import Expression
from compiler.classes.identifier import Identifier
from compiler.classes.link import Attribute
import copy
import numpy as np


def is_index_dependant_expression(expression, index) -> bool:

    e_type = expression.get_type()
    nb_child = expression.get_nb_children()
    children = expression.get_children()
    predicate: bool = False
    if e_type == 'literal':

        seed = expression.get_name()
        if type(seed) == Identifier:

            identifier = seed
            id_type = identifier.get_type()
            id_name = identifier.get_name()
            if id_type == "assign":

                predicate = is_index_dependant_expression(identifier.get_expression(), index)
            if id_name in index:

                predicate = True

        elif type(seed) == Attribute:

            attribute = seed
            identifier = attribute.get_attribute()
            if identifier.get_type() == "assign":

                predicate = is_index_dependant_expression(identifier.get_expression(), index)
    else:

        for i in range(nb_child):

            predicate_i = is_index_dependant_expression(children[i], index)
            if predicate_i:

                predicate = predicate_i
                break

    return predicate


class Factorize:

    def __init__(self, obj):

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

            return self.factorize_constraint(variables, constants, indexes)
        elif self.type_fact == "objective":

            return self.factorize_objective(variables, constants, indexes)
        else:

            return self.factorize_sum(variables, constants, indexes)

    def factorize_constraint(self, variables, constants, indexes):
        
        constraint = self.obj
        leaves_rhs = constraint.get_rhs().get_leafs()
        leaves_lhs = constraint.get_lhs().get_leafs()
        index_name = constraint.get_index_var() 
        self.index_list.append(index_name)
        var_leaves = []
        term_rhs, _ = self.compute_independant_term(constraint.get_rhs(), variables)
        term_lhs, _ = self.compute_independant_term(constraint.get_lhs(), variables)
        indep_term = Expression("-")
        indep_term.add_child(term_rhs)
        indep_term.add_child(term_lhs)
        self.set_indep_expr(indep_term)
        for leaf in leaves_rhs:

            inner_expr = leaf.get_name()
            l_type = leaf.get_type()
            if type(inner_expr) == Identifier:

                identifier = inner_expr
                id_name = identifier.get_name()
                if id_name in variables:

                    var = variables[id_name]
                    var_leaves.append([-1, leaf, identifier, var.get_index(), var.get_size()])
            
            if type(inner_expr) == Attribute:

                attribute = inner_expr
                attr_node = attribute.get_node_field()
                attr_id = attribute.get_attribute()
                if attr_node in variables:

                    dict_var_node = variables[attr_node]
                    id_name = attr_id.get_name()
                    if id_name in dict_var_node:

                        var = dict_var_node[id_name]
                        var_leaves.append([-1, leaf, attr_id, var.get_index(), var.get_size()])
            elif l_type == "sum":

                fct_constr = Factorize(leaf)
                is_var = fct_constr.factorize_sum(variables, constants, self.index_list)
                if is_var is True:
                    self.add_child([-1, fct_constr])
        
        for leaf in leaves_lhs:

            inner_expr = leaf.get_name()
            l_type = leaf.get_type()
            if type(inner_expr) == Identifier:

                identifier = inner_expr
                id_name = identifier.get_name()
                if id_name in variables:

                    var = variables[id_name]
                    var_leaves.append([1, leaf, identifier, var.get_index(), var.get_size()])
            if type(inner_expr) == Attribute:

                attribute = inner_expr
                attr_node = attribute.get_node_field()
                attr_id = attribute.get_attribute()
                if attr_node in variables:

                    dict_var_node = variables[attr_node]
                    id_name = attr_id.get_name()
                    if id_name in dict_var_node:

                        var = dict_var_node[id_name]
                        var_leaves.append([1, leaf, attr_id, var.get_index(), var.get_size()])
            elif l_type == "sum":

                fct_constr = Factorize(leaf)
                is_var = fct_constr.factorize_sum(variables, constants, self.index_list)
                if is_var is True:

                    self.add_child([1, fct_constr])
        coef_var = []
        for rhs_bool, leaf, identifier, index, var_size in var_leaves:

            parent = leaf.get_parent()
            expr = Expression('literal', 1, line=leaf.get_line())
            expr_coef, _ = self.compute_factor(expr, False, parent, leaf, constants)
            expr = identifier.get_expression()
            coef_var.append([rhs_bool, expr_coef, index, expr, var_size])
        self.coef_var_tuples = coef_var
        self.extension = self.extend(constants)

    def factorize_objective(self, variables, constants, indexes):

        objective = self.obj
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

                identifier = inner_expr
                id_name = identifier.get_name()
                if id_name in variables:

                    var = variables[id_name]
                    var_leaves.append([leaf, var.get_index(), var.get_size()])
            if l_type == "sum":

                fct_constr = Factorize(leaf)
                is_var = fct_constr.factorize_sum(variables, constants, self.index_list)
                if is_var is True:

                    self.add_child(fct_constr)
        coef_var = []
        for leaf, index, var_size in var_leaves:

            parent = leaf.get_parent()
            expr = Expression('literal', 1, line=leaf.get_line())
            expr_coef, _ = self.compute_factor(expr, False, parent, leaf, constants)
            identifier = leaf.get_name()
            expr = identifier.get_expression()
            coef_var.append([expr_coef, index, expr, var_size])
        self.coef_var_tuples = coef_var
        self.extension = self.extend(constants)

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

                identifier = inner_expr
                id_name = identifier.get_name()
                if id_name in variables:

                    var = variables[id_name]
                    var_leaves.append([leaf, var.get_index(), var.get_size()])
                    is_var = True
            elif type(inner_expr) == Attribute:

                attribute = inner_expr
                attr_node = attribute.get_node_field()
                attr_id = attribute.get_attribute()
                if attr_node in variables:

                    dict_var_node = variables[attr_node]
                    id_name = attr_id.get_name()
                    if id_name in dict_var_node:

                        var = dict_var_node[id_name]
                        var_leaves.append([leaf, var.get_index(), var.get_size()])
                        is_var = True
            if l_type == "sum":

                fct_constr = Factorize(leaf)
                is_var = fct_constr.factorize_sum(variables, constants, self.index_list)
                if is_var is True:

                    self.add_child(fct_constr)
                    is_var = True
        expr = Expression('literal', 1, line=expression_sum.get_line())
        parent = expression_sum.get_parent()
        expr_coef, _ = self.compute_factor(expr, False, parent, expression_sum, constants)
        self.mult_expr = expr_coef
        coef_var = []
        for leaf, index, var_size in var_leaves:

            parent = leaf.get_parent()
            expr = Expression('literal', 1, line=leaf.get_line())
            expr_coef, _ = self.compute_factor(expr, False, parent, leaf, constants, stop_expr=expression_sum)
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

                identifier = seed
                expr_name = identifier.get_name()
                if expr_name in variables:

                    is_var = True
                else:

                    expr_acc = copy.copy(expr)
            if type(seed) == Attribute:

                attribute = seed
                attr_node = attribute.get_node_field()
                attr_id = attribute.get_attribute()
                if attr_node in variables:
                
                    dict_var_node = variables[attr_node]
                    id_name = attr_id.get_name()
                    if id_name in dict_var_node:

                        is_var = True
                else:
                
                    expr_acc = copy.copy(expr)
        else:

            tuple_expr_is_var = []
            for child in children:

                expr_child, is_var_child = self.compute_independant_term(child, variables)
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
                elif var_1: 

                    expr_acc = expr1
                elif var_2:

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

    def compute_factor(self, expr_acc, is_index_dependant, parent_expr, branch_considered, constants, stop_expr=None):
        
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
            other_child_time_dependancy = is_index_dependant_expression(child, self.index_list)
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

    def extend(self, definitions):

        time_horizon = definitions["T"][0]
        unique_evaluation = False
        coef_var_tuples = self.coef_var_tuples 
        nb_coef_var = len(coef_var_tuples)
        flag_out_of_bounds = False
        children_sums = self.get_children()
        np_append = np.append
        list_values_columns = []
        list_values_columns_append = list_values_columns.append
        if self.type_fact == "constraint":

            constraint = self.obj
            b_expr = self.get_indep_expr()
            sign = constraint.get_sign()
            time_range = constraint.get_time_range(definitions)
            name_index = constraint.get_index_var()
            if time_range is None:

                t_horizon = time_horizon
                time_range = range(t_horizon)
            if (not is_index_dependant_expression(constraint.get_rhs(), name_index)) and \
                    (not is_index_dependant_expression(constraint.get_lhs(), name_index)):

                unique_evaluation = True
            for k in time_range:

                definitions[name_index] = [k]
                if constraint.check_time(definitions) is False:

                    continue
                new_values = np.zeros(nb_coef_var)
                columns = np.zeros(nb_coef_var)
                i = 0
                for mult_sign, expr_coef, index, offset_expr, max_size in coef_var_tuples:

                    new_values[i] = mult_sign*expr_coef.evaluate_expression(definitions)
                    if offset_expr is not None:

                        offset = offset_expr.evaluate_expression(definitions)
                    else:

                        offset = 0
                    if (offset < 0) or (offset >= max_size):

                        flag_out_of_bounds = True
                        break
                    columns[i] = index + offset
                    i = i+1
                if not flag_out_of_bounds:

                    for sign, child in children_sums:

                        tuple_val_col = child.extend(definitions)
                        if not tuple_val_col:

                            error_("Out of bounds sum at line "+str(constraint.get_line()))
                        child_values, child_columns = tuple_val_col
                        child_values = sign * child_values
                        new_values = np_append(new_values, child_values)
                        columns = np_append(columns, child_columns)
                    if b_expr is not None:

                        constant = b_expr.evaluate_expression(definitions)
                    else:

                        constant = 0
                    matrix = [new_values, columns]
                    list_values_columns_append([matrix, constant, sign])
                    if unique_evaluation is True:

                        break
            if name_index in definitions:

                definitions.pop(name_index)
        elif self.type_fact == "objective":

            objective = self.obj
            obj_expr = objective.get_expression()
            obj_range = objective.get_time_range(definitions)
            name_index = objective.get_index_var()
            obj_type = objective.get_type()
            b_expr = self.get_indep_expr()

            if obj_range is None:

                t_horizon = time_horizon
                obj_range = range(t_horizon)
            if not is_index_dependant_expression(obj_expr, name_index):

                unique_evaluation = True
            for k in obj_range:

                definitions[name_index] = [k]
                if objective.check_time(definitions) is False:

                    continue
                new_values = np.zeros(nb_coef_var)
                columns = np.zeros(nb_coef_var)
                i = 0
                for expr_coef, index, offset_expr, max_size in coef_var_tuples:

                    new_values[i] = expr_coef.evaluate_expression(definitions)
                    if offset_expr is not None:

                        offset = offset_expr.evaluate_expression(definitions)
                    else:

                        offset = 0
                    if (offset < 0) or (offset >= max_size):

                        flag_out_of_bounds = True
                        break
                    columns[i] = index + offset
                    i = i+1
                if not flag_out_of_bounds:

                    for child in children_sums:

                        tuple_val_col = child.extend(definitions)
                        if not tuple_val_col:

                            error_("Out of bounds sum at line "+str(objective.get_line()))
                        child_values, child_columns = tuple_val_col
                        new_values = np.append(new_values, child_values)
                        columns = np.append(columns, child_columns)

                    constant = b_expr.evaluate_expression(definitions)
                    matrix = [new_values, columns]
                    list_values_columns.append([matrix, constant, obj_type])
                    if unique_evaluation is True:

                        break
            if name_index in definitions:

                definitions.pop(name_index)

        elif self.type_fact == "sum":

            expr_sum = self.obj
            time_interval = expr_sum.get_time_interval()
            name_index = time_interval.get_index_name()
            range_index = time_interval.get_range(definitions)
            new_values = np.zeros(nb_coef_var*len(range_index))
            columns = np.zeros(nb_coef_var*len(range_index))
            multiplicator = self.mult_expr.evaluate_expression(definitions)

            i = 0
            for k in range_index:

                definitions[name_index] = [k]
                for expr_coef, index, offset_expr, max_size in coef_var_tuples:

                    new_values[i] = expr_coef.evaluate_expression(definitions)
                    if offset_expr is not None:

                        offset = offset_expr.evaluate_expression(definitions)
                    else:

                        offset = 0
                    if (offset < 0) or (offset >= max_size):

                        flag_out_of_bounds = True
                        break
                    columns[i] = index + offset
                    i = i+1
                if flag_out_of_bounds:
                    
                    break
            if not flag_out_of_bounds:
                
                for child in children_sums:

                    for k in range_index: 

                        definitions[name_index] = [k]
                        tuple_val_col = child.extend(definitions)
                        if not tuple_val_col:

                            error_("Out of bounds sum at line "+str(expr_sum.get_line()))
                        child_values, child_columns = tuple_val_col
                        new_values = np.append(new_values, child_values)
                        columns = np.append(columns, child_columns)
                new_values = new_values*multiplicator
                list_values_columns = [new_values, columns]
            if name_index in definitions:

                definitions.pop(name_index)
        
        return list_values_columns