
# gboml_semantic.py
#
# Part of the GBOML Project
# University of Liege
# Writer : MIFTARI B
# ------------


from .classes import Expression, Attribute, Program, Node, Identifier, Factorize, Hyperlink, Variable, Sizing, State, \
    Action, Auxiliary, MDPObjective, MDP, Time, Parameter
from .classes.error import RedefinitionError

import numpy as np  # type: ignore
from .utils import error_
import time as t


def new_semantic(program: Program) -> Program:

    time = program.get_time()
    check_time_horizon(time)
    time_value = time.get_value()

    node_list = program.get_nodes()
    link_list = program.get_links()
    check_names_repetitions(node_list+link_list)

    definitions = dict()
    time_parameter = Parameter("T", Expression("literal", time_value))
    time_parameter.set_value([time_value])

    definitions["T"] = time_parameter
    global_param = program.get_dict_global_parameters()
    parameter_evaluation(global_param, definitions)
    definitions["global"] = global_param
    program_variables_dict = {}

    global_index = 0

    for node in node_list:
        name = node.get_name()

        # Retrieve node parameter dictionary
        node_parameters = node.get_dictionary_parameters()
        node_variables = node.get_dictionary_variables(get_id=False)
        match_dictionaries(node_parameters, node_variables)
        parameter_evaluation(node_parameters, global_param)
        definitions[name] = node_parameters
        program_variables_dict[name] = node_variables
        global_index = set_size_variables(node_variables, definitions, global_index)

    for link in link_list:
        name = link.get_name()
        link_parameters = link.get_dictionary_parameters()
        parameter_evaluation(link_parameters, global_param)
        definitions[name] = link_parameters

    for node in node_list:
        name = node.get_name()
        start_time = t.time()
        add_node_names(node)
        check_definition(node, program_variables_dict, definitions)
        replace_parameters_node(node, definitions)
        check_expressions_dependancy_rl(node, variables_dict=program_variables_dict)
        print("Check variables of node %s : --- %s seconds ---" % (name, t.time() - start_time))

    for link in link_list:
        name = link.get_name()
        start_time = t.time()
        add_link_names(link)
        check_definition_link(link, program_variables_dict, definitions)
        replace_parameters_hyperlinks(link, definitions)
        check_link_rl(link, program_variables_dict)
        print("Check hyperlink %s : --- %s seconds ---" % (name, t.time() - start_time))

    check_all_variables(program_variables_dict)
    mdp = convert_to_mdp(program, program_variables_dict)
    exit()
    return program


def replace_parameters_hyperlinks(hyperlink: Hyperlink, definitions):
    constraints = hyperlink.get_constraints()
    for constraint in constraints:
        rhs: Expression = constraint.get_rhs()
        lhs: Expression = constraint.get_lhs()
        rhs.replace_basic_parameters(definitions)
        lhs.replace_basic_parameters(definitions)


def replace_parameters_node(node: Node, definitions):
    constraints = node.get_constraints()
    objectives = node.get_objectives()
    for constraint in constraints:
        rhs: Expression = constraint.get_rhs()
        lhs: Expression = constraint.get_lhs()
        rhs.replace_basic_parameters(definitions)
        lhs.replace_basic_parameters(definitions)

    for objective in objectives:
        obj_expression: Expression = objective.get_expression()
        obj_expression.replace_basic_parameters(definitions)


def check_definition_link(link: Hyperlink, variables_dict: dict, parameters_dict: dict):
    constraints_list = link.get_constraints()
    link_name = link.get_name()

    for constraint in constraints_list:
        index_var = constraint.get_index_var()
        reserved = [index_var]
        lhs = constraint.get_lhs()
        check_definition_expression(lhs, variables_dict, parameters_dict, reserved, in_node_name_parameter=link_name)
        rhs = constraint.get_rhs()
        check_definition_expression(rhs, variables_dict, parameters_dict, reserved, in_node_name_parameter=link_name)


def check_definition(node: Node, variables_dict: dict, parameters_dict: dict):
    objectives_list = node.get_objectives()
    constraints_list = node.get_constraints()
    node_name = node.get_name()

    for constraint in constraints_list:
        index_var = constraint.get_index_var()
        reserved = [index_var]
        lhs = constraint.get_lhs()
        check_definition_expression(lhs, variables_dict, parameters_dict, reserved,
                                    in_node_name_variable=node_name, in_node_name_parameter=node_name)
        rhs = constraint.get_rhs()
        check_definition_expression(rhs, variables_dict, parameters_dict, reserved,
                                    in_node_name_variable=node_name, in_node_name_parameter=node_name)

    for objective in objectives_list:
        expr = objective.get_expression()
        index_var = objective.get_index_var()
        reserved = [index_var]
        check_definition_expression(expr, variables_dict, parameters_dict, reserved,
                                    in_node_name_variable=node_name, in_node_name_parameter=node_name)


def check_definition_expression(expr: Expression, variables_dict: dict, parameters_dict: dict, reserved=[],
                                variables_allowed=True, in_node_name_variable="", in_node_name_parameter=""):
    leaves = expr.get_leafs()
    for leaf in leaves:
        in_node_name = ""
        is_reserved = False
        seed = leaf.get_name()
        if type(seed) == Identifier:
            defined = False
            seed_identifier: Identifier = seed
            seed_node_name = seed_identifier.get_node_name()
            seed_id_name = seed_identifier.get_name()

            if seed_node_name == "" and (seed_id_name in reserved or seed_id_name == "T"):
                defined = True
                is_reserved = True
            elif seed_node_name in variables_dict and seed_id_name in variables_dict[seed_node_name]:
                defined = True
                in_node_name = in_node_name_variable
                variable_referenced: Variable = variables_dict[seed_node_name][seed_id_name]
                identifier_referenced = variable_referenced.get_identifier()
                identifier_referenced_type = identifier_referenced.get_type()
                if not variables_allowed:
                    error_("ERROR: variables are not allowed in brackets at line "+str(leaf.get_line()))

                if seed_identifier.get_type() != identifier_referenced_type:
                    error_("ERROR: Unmatching type between definition of "+str(identifier_referenced) +
                           " and usage "+str(seed_identifier)+" at line "+str(seed.get_line()))

            elif seed_node_name in parameters_dict and seed_id_name in parameters_dict[seed_node_name]:
                parameter_referenced: Parameter = parameters_dict[seed_node_name][seed_id_name]
                parameter_referenced_type = parameter_referenced.get_type()
                defined = True
                in_node_name = in_node_name_parameter
                identifier_referenced_type = ""
                if parameter_referenced_type == "expression":
                    identifier_referenced_type = "basic"
                elif parameter_referenced_type == "table":
                    identifier_referenced_type = "assign"

                if seed_identifier.get_type() != identifier_referenced_type:
                    error_("ERROR: Unmatching type between definition of "+str(seed_id_name) +
                           " and usage "+str(seed_identifier)+" at line "+str(seed.get_line()))

            if not defined:
                error_("ERROR: Unknown identifier " + str(seed_identifier) + " at line "+str(leaf.get_line()))

            elif not is_reserved and \
                    in_node_name != "" and\
                    seed_node_name != "global" and\
                    in_node_name != seed_node_name:

                error_("ERROR: referencing variables or parameters defined in node "+str(seed_node_name) +
                       " inside node "+str(in_node_name)+" is not allowed at line "+str(expr.get_line()))

            expression_in_brackets = seed_identifier.get_expression()
            if expression_in_brackets is not None:
                check_definition_expression(expression_in_brackets, variables_dict, parameters_dict, reserved,
                                            variables_allowed=False, in_node_name_variable=in_node_name_variable,
                                            in_node_name_parameter=in_node_name_parameter)

        if leaf.get_type() == "sum":
            sum_expr: Expression = leaf
            sum_children = sum_expr.get_children()
            time_interval = sum_expr.get_time_interval()
            index_name = time_interval.get_index_name()

            if in_node_name in variables_dict and index_name in variables_dict[in_node_name]:
                error_("ERROR: Redefinition of variable name by index "+str(index_name) +
                       " at line "+str(leaf.get_line()))

            if in_node_name in parameters_dict and index_name in parameters_dict[in_node_name]:
                error_("ERROR: Redefinition of parameter name by index "+str(index_name) +
                       " at line "+str(leaf.get_line()))

            reserved_sum = reserved + [index_name]
            for child in sum_children:
                check_definition_expression(child, variables_dict, parameters_dict, reserved_sum,
                                            variables_allowed, in_node_name_variable, in_node_name_parameter)


def add_link_names(link: Hyperlink):
    constraints_list = link.get_constraints()

    for constraint in constraints_list:
        lhs = constraint.get_lhs()
        index_var = constraint.get_index_var()

        reserved = [index_var]
        add_node_names_expression(lhs, link, reserved)
        rhs = constraint.get_rhs()
        add_node_names_expression(rhs, link, reserved)


def add_node_names(node: Node):
    objectives_list = node.get_objectives()
    constraints_list = node.get_constraints()

    for constraint in constraints_list:
        lhs = constraint.get_lhs()
        index_var = constraint.get_index_var()

        reserved = [index_var]
        add_node_names_expression(lhs, node, reserved)
        rhs = constraint.get_rhs()
        add_node_names_expression(rhs, node, reserved)

    for objective in objectives_list:
        expr = objective.get_expression()
        index_var = objective.get_index_var()
        reserved = [index_var]
        add_node_names_expression(expr, node, reserved)


def add_node_names_expression(expr: Expression, node, reserved_identifiers=[]):
    leaves = expr.get_leafs()
    reserved = ["T"]+reserved_identifiers
    for leaf in leaves:
        seed = leaf.get_name()
        if type(seed) == Identifier:
            identifier: Identifier = seed
            if identifier.get_node_name() == "" and identifier.get_name() not in reserved:
                identifier.set_node(node)

        if leaf.get_type() == "sum":
            sum_expr: Expression = leaf
            sum_children = sum_expr.get_children()
            time_interval = sum_expr.get_time_interval()
            index_name = time_interval.get_index_name()
            reserved_sum = reserved + [index_name]
            for child in sum_children:
                add_node_names_expression(child, node, reserved_sum)


def check_time_horizon(time_horizon: Time):

    variable_name = time_horizon.get_name()

    if variable_name != "T":
        error_("Semantic error:" + str(line) + ": Use \"T\"" + " as a symbol for the time horizon. \""
               + str(variable_name) + "\" is not allowed")

    time_value = time_horizon.get_value()
    if type(time_value) == float and time_value.is_integer() is False:

        time_value = int(round(time_value))
        print("WARNING: the time horizon considered is not an int")
        print("The time horizon was rounded to "+str(time_value))
    elif type(time_value) == float:

        time_value = int(time_value)
    if time_value < 0:

        error_("ERROR: the chosen time horizon is negative.")
    elif time_value == 0:

        print("WARNING: the time horizon considered is 0")

    time_horizon.set_value(time_value)


def convert_to_mdp(program, program_variables_dict):
    list_states = []
    list_auxiliaries = []
    list_actions = []
    list_sizing = []
    list_mdpobjectives = []
    nodes = program.get_nodes()

    for node_name in program_variables_dict.keys():
        node_variables_dict = program_variables_dict[node_name]
        for variable_name in node_variables_dict.keys():
            variable = node_variables_dict[variable_name]
            var_option = variable.get_option()
            if var_option == "state":
                state_var = State(variable_name, node_name, variable.get_dynamic(), variable.get_initial_constraint())
                list_states.append(state_var)

            elif var_option == "sizing":
                sizing_var = Sizing(variable_name, node_name, variable.get_lower_constraint(),
                                    variable.get_upper_constraint())
                list_sizing.append(sizing_var)

            elif var_option == "action":
                action_var = Action(variable_name, node_name, variable.get_lower_constraint(),
                                    variable.get_upper_constraint())
                list_actions.append(action_var)

            elif var_option == "auxiliary":
                aux_var = Auxiliary(variable_name, node_name, variable.get_assignment())
                list_auxiliaries.append(aux_var)

    for node in nodes:
        node_name = node.get_name()
        node_obj = node.get_objectives()
        for objective in node_obj:
            mdp_objective = MDPObjective(node_name, objective.get_expression())
            list_mdpobjectives.append(mdp_objective)

    mdp = MDP(list_states, list_actions, list_sizing, list_auxiliaries, list_mdpobjectives)
    return mdp


def check_all_variables(program_variables_dict):
    error_message = ""
    raised_error = False
    for node_name in program_variables_dict.keys():
        node_variables_dict = program_variables_dict[node_name]
        for variable_name in node_variables_dict.keys():
            variable = node_variables_dict[variable_name]
            var_option = variable.get_option()
            if var_option == "state":
                dynamic = variable.get_dynamic()
                initial = variable.get_initial_constraint()
                if dynamic is None or initial is None:
                    error_message += "\nERROR: State variable "+str(variable_name) + " in node "+str(node_name) + \
                                    " is not properly defined : "

                    if dynamic is None:
                        error_message += "\n- the dynamic is missing"
                    if initial is None:
                        error_message += "\n- the initial condition is missing"

                    raised_error = True

            elif var_option == "action" or var_option == "sizing":
                lower_bound = variable.get_lower_constraint()
                upper_bound = variable.get_upper_constraint()
                if lower_bound is None or upper_bound is None:
                    error_message += "\nWarning: "+str(var_option).title() + " variable "\
                                     + str(variable_name) + " in node "+str(node_name) + " is not properly defined : "

                    if lower_bound is None:
                        error_message += "\n- A lower bound is missing"

                    if upper_bound is None:
                        error_message += "\n- An upper bound is missing"

            elif var_option == "auxiliary":
                assignment = variable.get_assignment()
                if assignment is None:
                    error_message += "\nERROR: Auxiliary variable " + str(variable_name) + " in node " \
                                     + str(node_name) + " is not properly defined : "
                    error_message += "\n- An assignment is missing"
                    raised_error = True
                circular_ref = check_circular_ref(variable, list())
                if circular_ref:
                    error_message += "\nERROR: Auxiliary variable " + str(variable_name) \
                                     + "'s definition contains a circular reference"
                    raised_error = True

    if raised_error:
        error_(error_message)
    else:
        print(error_message)


def check_circular_ref(variable: Variable, set_explored: list):
    list_aux = variable.get_dependencies()
    set_explored.append(variable)
    circular_ref = False
    for aux_var in list_aux:
        if aux_var in set_explored:
            circular_ref = True
        else:
            circular_ref = check_circular_ref(aux_var, set_explored)

        if circular_ref:
            break
    _ = set_explored.pop()
    return circular_ref


def free_non_useful_information_in_hyperlink(hyperlink):
    constraints = hyperlink.get_constraints()

    for constraint in constraints:
        constraint.rhs.free()
        constraint.rhs = None
        constraint.lhs.free()
        constraint.lhs = None


def free_non_useful_information_in_node(node):
    constraints = node.get_constraints()
    objectives = node.get_objectives()
    for constraint in constraints:
        constraint.rhs.free()
        constraint.rhs = None
        constraint.lhs.free()
        constraint.lhs = None
    for objective in objectives:
        objective.expression.free()
        objective.expression = None

#
# Name checking functions
#


def match_dictionaries(dict1: dict, dict2: dict) -> None:
    """
    Match dictionaries find the intersection between the keys of two dictionaries
    returns nothing if set is empty and outputs an error otherwise
    INPUT:  dict1 -> dictionary
            dict2 -> dictionary
    OUTPUT: None, or error if fails
    """
    dict1_set = set(dict1)
    dict2_set = set(dict2)

    inter_set = dict1_set.intersection(dict2_set)  
 
    if len(inter_set) != 0:
        error_("ERROR : some variables and parameters share the same name: "+str(inter_set))


def check_names_repetitions(elements_list: list) -> None:
    """
    Checks if a node name is present twice in a list of nodes
    INPUT:  elements_list -> list of node objects
    OUTPUT: None, or error if fails
    """

    n = len(elements_list)
    i = 0

    for e in elements_list:
        name = e.get_name()

        if name == "T" or name == "t":
            error_('ERROR: Name "'+str(name)+'" is reserved for time, used at line '+str(elements_list[i].get_line()))

        for k in range(i+1, n):
            if name == elements_list[k].get_name():
                error_('ERROR: Redefinition error: "'+str(name)+'" at line '+str(elements_list[k].get_line()))
        i = i+1


#
# End Name checking functions
#


#
# Link functions
#


def check_link_rl(hyperlink: Hyperlink, var_obj: dict) -> list:
    """
    check_link function : Takes program object and checks its links
    INPUT:  program -> Program object
    OUTPUT: list of input output pairs 
    """

    links = hyperlink.get_constraints()
    list_factor = []
    for link in links:
        if link.get_time_interval() or link.get_condition():
            error_("ERROR: adding a time range is not allowed in MDP definition at line " + link.get_line())

        rhs = link.get_rhs()
        lhs = link.get_lhs()
        link_type = link.get_type()
        var_in_right = predicate_variables_in_expression(rhs, var_obj)
        var_in_left = predicate_variables_in_expression(lhs, var_obj)

        if link_type == "==":
            # Either auxiliary assignment of auxiliary or a dynamic definition
            if not var_in_left:
                error_("The left-hand-side should contain a variable at line "+str(link.get_line()))
            variable, time_dep, node_name = check_lhs_equality(lhs, var_obj)
            var_option = variable.get_option()
            if var_option == "state":
                if time_dep != 2 and time_dep != 0:
                    error_("ERROR: can not assign a state at another timestep than 't+1' at line "
                           + str(constraint.get_line()))
                if time_dep == 2:
                    check_rhs_equality_states(rhs, var_obj, variable, node_name)
                    try:
                        variable.set_dynamic(rhs)
                    except RedefinitionError:
                        error_("Error: redefinition of dynamic for variable " + str(variable) +
                               " at line " + str(link.get_line()))
                if time_dep == 0 and var_in_right:
                    error_("ERROR: No variable can be used to define an intial condition at line "
                           + str(constraint.get_line()))
                elif time_dep == 0:
                    try:
                        variable.set_initial_constraint(rhs)
                    except RedefinitionError:
                        error_("Error: redefinition of dynamic for variable " + str(variable) +
                               " at line " + str(link.get_line()))

            elif var_option == "auxiliary":
                if time_dep != 1:
                    error_("ERROR : An auxiliary variable can only be assigned at index t at line "
                           + str(link.get_line()))
                list_aux = check_rhs_equality_auxiliary(rhs, var_obj, variable, node_name)
                try:
                    variable.set_assignment(rhs)
                    variable.set_dependencies(list_aux)
                except RedefinitionError:
                    error_("Error: redefinition of dynamic for variable " + str(variable) +
                           " at line " + str(link.get_line()))
            else:
                error_("ERROR: assignments can only be used for auxiliaries or states at line "+str(link.get_line()))
        elif link_type == "<=" or link_type == ">=":
            if var_in_right and var_in_left:
                error_("ERROR : the left and right hand-side of an inequality can not contain variables at line "
                       + str(link.get_line()))
            elif var_in_right:
                variable, _ = check_variable_inequality(rhs, var_obj)
                try:
                    if link_type == "<=":
                        variable.set_lower_constraint(lhs)
                    if link_type == ">=":
                        variable.set_upper_constraint(lhs)
                except RedefinitionError:
                    error_("Error: redefinition of lower-bound for variable " + str(variable) +
                           " at line " + str(link.get_line()))

            elif var_in_left:
                variable, _ = check_variable_inequality(lhs, var_obj)
                try:
                    if link_type == "<=":
                        variable.set_upper_constraint(rhs)
                    if link_type == ">=":
                        variable.set_lower_constraint(rhs)
                except RedefinitionError:
                    error_("Error: redefinition of lower-bound for variable " + str(variable) +
                           " at line " + str(link.get_line()))

            else:
                error_("ERROR: No variable in constraint at line "+str(constraint.get_line()))
    return list_factor

#
# End link functions
#

#
# Node checking functions
#


def set_size_variables(dictionary_var: dict, dictionary_param: dict, index: int) -> int:
    """
    Initializes the index of variable object inside a dictionary
    """
    start_index = index
    timehorizon = dictionary_param["T"].get_value()[0]
    for k in dictionary_var.keys():
        var = dictionary_var[k]
        identifier = var.get_identifier()
        identifier.set_size(dictionary_param)
        v_size = var.get_size()
        v_type = var.get_option()

        if v_type == "auxiliary" and v_size != timehorizon:
            error_("ERROR: auxiliary variables must have a size of T at line "+str(var.get_line()))

        elif v_type == "state" and v_size != timehorizon:
            error_("ERROR: state variables must have a size of T at line "+str(var.get_line()))

        elif v_type == "sizing" and v_size != 1:
            error_("ERROR: sizing variables must have a size of 1 at line "+str(var.get_line()))

        start_index = identifier.set_index(start_index)
    return start_index


def check_expressions_dependancy_rl(node: Node, variables_dict: dict):
    constraints = node.get_constraints()
    objectives = node.get_objectives()
    node_name = node.get_name()
    for constraint in constraints:
        if constraint.get_time_interval() or constraint.get_condition():
            error_("ERROR: adding a time range is not allowed in MDP definition at line "+constraint.get_line())

        rhs = constraint.get_rhs()
        lhs = constraint.get_lhs()
        constr_type = constraint.get_type()
        var_in_right = predicate_variables_in_expression(rhs, variables_dict)
        var_in_left = predicate_variables_in_expression(lhs, variables_dict)

        if constr_type == "==":
            # Either auxiliary assignment of auxiliary or a dynamic definition

            variable, time_dep, _ = check_lhs_equality(lhs, variables_dict)
            var_option = variable.get_option()
            if var_option == "state":
                if time_dep != 2 and time_dep != 0:
                    error_("ERROR: can not assign a state at another timestep than 't+1' at line "
                           + str(constraint.get_line()))
                if time_dep == 2:
                    check_rhs_equality_states(rhs, variables_dict, variable, var_node_name=node_name)
                    try:
                        variable.set_dynamic(rhs)
                    except RedefinitionError:
                        error_("Error: redefinition of dynamic for variable "+str(variable) +
                               " at line "+str(constraint.get_line()))
                if time_dep == 0 and var_in_right:
                    error_("ERROR: No variable can be used to define an intial condition at line "
                           + str(constraint.get_line()))
                elif time_dep == 0:
                    try:
                        variable.set_initial_constraint(rhs)
                    except RedefinitionError:
                        error_("Error: redefinition of dynamic for variable " + str(variable) +
                               " at line " + str(constraint.get_line()))
            elif var_option == "auxiliary":
                if time_dep != 1:
                    error_("ERROR: can not assign an auxiliary at another timestep than 't' at line "
                           + str(constraint.get_line()))
                list_aux = check_rhs_equality_auxiliary(rhs, variables_dict, variable)
                try:
                    variable.set_assignment(rhs)
                    variable.set_dependencies(list_aux)
                except RedefinitionError:
                    error_("Error: redefinition of dynamic for variable "+str(variable) +
                           " at line "+str(constraint.get_line()))
            else:
                error_("ERROR: assignments can only be used for auxiliaries or states at line "
                       + str(constraint.get_line()))

        elif constr_type == "<=" or constr_type == ">=":
            if var_in_right and var_in_left:
                error_("ERROR : the left and right hand-side of an inequality can not contain variables at line "
                       + str(constraint.get_line()))
            elif var_in_right:
                variable, _ = check_variable_inequality(rhs, variables_dict)
                try:
                    if constr_type == "<=":
                        variable.set_lower_constraint(lhs)
                    if constr_type == ">=":
                        variable.set_upper_constraint(lhs)
                except RedefinitionError:
                    error_("Error: redefinition of lower-bound for variable " + str(variable) +
                           " at line " + str(constraint.get_line()))

            elif var_in_left:
                variable, _ = check_variable_inequality(lhs, variables_dict)
                try:
                    if constr_type == "<=":
                        variable.set_upper_constraint(rhs)
                    if constr_type == ">=":
                        variable.set_lower_constraint(rhs)
                except RedefinitionError:
                    error_("Error: redefinition of lower-bound for variable " + str(variable) +
                           " at line " + str(constraint.get_line()))

            else:
                error_("ERROR: No variable in constraint at line "+str(constraint.get_line()))

    for objective in objectives:
        expr = objective.get_expression()
        check_objective(expr, variables_dict)


def check_objective(expression: Expression, var_dict: dict):
    leaves = expression.get_leafs()
    list_var = []

    for leaf in leaves:

        seed = leaf.get_name()
        if type(seed) == Identifier:
            l_name = seed.get_name()

            if l_name in var_dict:
                variable_leaf = var_dict[l_name]
                time_dep = check_time_dependancy(seed)
                if time_dep != 1 and time_dep != -1:
                    error_("ERROR: term " + str(seed) + " at that timestep is not allowed for the definition of "
                                                        "auxiliaries at line " + str(seed.get_line()))

                list_var.append(variable_leaf)

    return list_var


def check_rhs_equality_auxiliary(rhs: Expression, var_dict: dict, variable: Variable, var_node_name=""):
    leaves = rhs.get_leafs()
    list_aux = []
    var_id = variable.get_identifier()
    var_name = var_id.get_name()

    for leaf in leaves:

        seed = leaf.get_name()
        node_var = var_dict

        if type(seed) == Identifier:
            identifier: Identifier = seed
            id_name = identifier.get_name()
            node_name = identifier.get_node_name()
            if node_name in var_dict:
                node_var = var_dict[node_name]

            if id_name in node_var:
                variable_leaf = node_var[id_name]
                option = variable_leaf.get_option()
                time_dep = check_time_dependancy(identifier)
                if time_dep != 1 and time_dep != -1:
                    error_("ERROR: term " + str(seed) + " at that timestep is not allowed for the definition of "
                                                        "auxiliaries at line " + str(seed.get_line()))

                if option == "auxiliary":
                    if id_name == var_name and node_name == var_node_name:
                        error_("ERROR: left-hand-side and right-hand-side contain the same term at line "
                               + str(seed.get_line()))

                    list_aux.append(variable_leaf)

    return list_aux


def check_rhs_equality_states(rhs: Expression, var_dict: dict, variable, var_node_name=""):
    leaves = rhs.get_leafs()

    var_id: Identifier = variable.get_name()
    var_name = var_id.get_name()

    time_dep = None
    is_state = False
    is_action = False
    previous_step = False

    for leaf in leaves:

        seed = leaf.get_name()
        node_dict = var_dict
        if type(seed) == Identifier:
            identifier: Identifier = seed
            identifier_name = identifier.get_name()
            node_name = identifier.get_node_name()
            if node_name in var_dict:
                node_dict = var_dict[node_name]

            if identifier_name in node_dict:
                variable = node_dict[identifier_name]
                option = variable.get_option()

                if option == "action":
                    is_action = True

                elif option == "state":
                    is_state = True
                    if identifier_name == var_name and node_name == var_node_name:

                        previous_step = True

                time_dep = check_time_dependancy(identifier)

                if time_dep != 1:
                    error_("ERROR: term "+str(seed)+" at that timestep is not allowed for the definition of "
                                                    "dynamics at line "+str(seed.get_line()))

    if is_action is not True or previous_step is not True:
        error_message = "ERROR : dynamic at line: " + str(rhs.get_line()) + " is ill-defined :"

        if is_action is not True:
            error_message += "\n- an action is missing"
        if previous_step is not True:
            error_message += "\n- the previous state is missing"
        if is_state is not True:
            error_message += "\n- No state is used"
        error_(error_message)

    return variable, time_dep


def check_lhs_equality(lhs: Expression, var_dict: dict):
    leaves = lhs.get_leafs()
    variable = None
    time_dep = None
    node_name = ""
    if len(leaves) != 1:
        error_("ERROR: not only a single left-hand-side variable is allowed in constraints "
               "at line " + str(lhs.get_line()))

    for leaf in leaves:
        seed = leaf.get_name()
        if type(seed) == Identifier:
            identifier: Identifier = seed
            identifier_name = identifier.get_name()
            identifier_node_name = identifier.get_node_name()
            if identifier_node_name in var_dict and identifier_name in var_dict[identifier_node_name]:
                variable = var_dict[identifier_node_name][identifier_name]
                time_dep = check_time_dependancy(identifier)

            else:
                error_("ERROR: not allowed to use anything but variables in the left-hand-side "
                       "of equality constraints at line "+str(lhs.get_line()))

        else:
            error_("ERROR: not allowed to use anything but variables in the left-hand-side "
                   "of equality constraints at line " + str(lhs.get_line()))

    return variable, time_dep, node_name


def check_variable_inequality(expr: Expression, var_dict: dict):
    leaves = expr.get_leafs()
    variable = None
    time_dep = None

    if len(leaves) != 1:
        error_("ERROR: only a single variable is allowed in constraints "
               "at line " + str(expr.get_line()))

    for leaf in leaves:

        seed = leaf.get_name()
        node_dict = var_dict

        if type(seed) == Identifier:
            identifier: Identifier = seed
            node_name = identifier.get_node_name()
            id_name = identifier.get_name()
            if node_name in var_dict:
                node_dict = var_dict[node_name]

            if id_name in node_dict:
                variable = node_dict[id_name]
                option = variable.get_option()
                if option != "sizing" and option != "action":
                    error_("ERROR: only action and sizing variables can be concerned with inequality constraints")
                time_dep = check_time_dependancy(identifier)
                if option == "sizing" and time_dep != -1:
                    error_("Error: sizing variables "+str(leaf)+" must be not indexed at line "+str(leaf.get_line()))
                if option == "action" and time_dep != 1:
                    error_("Error: action variables "+str(leaf)+" must be indexed at t at line "+str(leaf.get_line()))

            else:
                error_("ERROR: not allowed to use anything but variables in the inequality "
                       "constraints at line " + str(expr.get_line()))

    return variable, time_dep


def check_time_dependancy(seed):

    seed_type = seed.get_type()
    return_value = 0
    if seed_type == "basic":
        return_value = -1

    elif seed_type == "assign":
        expr = seed.get_expression()
        expr_type = expr.get_type()
        if expr_type == "literal":
            identifier = expr.get_name()
            if type(identifier) == int or type(identifier) == float:
                value = identifier
                if value != 0:
                    error_("ERROR : constants other than 0 are not allowed as in bracket expression at line "
                           + str(expr.get_line()))

            elif identifier.get_name() != "t":

                error_("ERROR : the in bracket expression can not be a parameter" + str(identifier.get_name()))

            else:
                return_value = 1

        elif expr_type == "+":
            child_1, child_2 = expr.get_children()
            child_1_type = child_1.get_type()
            child_2_type = child_2.get_type()
            child_1_identifier = child_1.get_name()
            child_2_identifier = child_2.get_name()
            rhs_number = False
            lhs_number = False

            if child_1_type != "literal" or child_2_type != "literal":
                error_('ERROR: the assignment '+str(expr)+' is not allowed at line '+str(expr.get_line()))

            if type(child_1_identifier) == int or type(child_1_identifier) == float:
                value = child_1_identifier
                if value != 1:
                    error_("ERROR : constants other than 0 are not allowed as in bracket expression at line "
                           + str(expr.get_line()))
                lhs_number = True

            elif child_1_identifier.get_name() != "t":

                error_("ERROR : the in bracket expression can not be a parameter" + str(child_1_identifier.get_name()))

            if (type(child_2_identifier) == int or type(child_2_identifier) == float) and not rhs_number:
                value = child_2_identifier
                if value != 1:
                    error_("ERROR : constants other than 0 are not allowed as in bracket expression at line "
                           + str(expr.get_line()))
                rhs_number = True

            elif child_2_identifier.get_name() != "t":

                error_("ERROR : the in bracket expression can not be a parameter" + str(child_2_identifier.get_name()))

            if (lhs_number or rhs_number) and not (lhs_number and rhs_number):

                return_value = 2

            else:
                error_('ERROR: the assignment '+str(expr)+' is not allowed at line '+str(expr.get_line()))

        else:
            error_('ERROR: the assignment '+str(expr)+' is not allowed at line '+str(expr.get_line()))
    return return_value


def predicate_variables_in_expression(expression: Expression, variables: dict) -> bool:
    """
    variables_in_expression function : returns true if expression contains variables and false otherwise
    INPUT:  expression -> expression object
            variables -> dictionary of <name,identifier> objects
            parameters -> dictionary of <name,array> objects 
            check_in -> check for errors in identifier 's assigned expression
    OUTPUT: bool -> boolean value if expression contains variable
    """

    leaves = expression.get_leafs()
    is_variable: bool = False

    for leaf in leaves:
        seed = leaf.get_name()
        leaf_type = leaf.get_type()
        if type(seed) == Identifier:
            identifier: Identifier = seed
            identifier_name = identifier.get_name()
            identifier_node_name = identifier.get_node_name()
            if identifier_node_name in variables and identifier_name in variables[identifier_node_name]:
                is_variable = True
                break

        elif leaf_type == 'sum':

            children_of_sum = leaf.get_children()
            for child in children_of_sum:

                is_child_var = predicate_variables_in_expression(child, variables)
                if is_child_var is True:

                    is_variable = True
                    break

    return is_variable


def parameter_evaluation(parameter_dict: dict, definitions: dict):
    """
    parameter_evaluation function : evaluates a list of parameter objects
    INPUT:  n_parameters -> list of parameters objects
            definitions -> dictionary of definitions <name,array>
    OUTPUT: definitions -> dictionary of definitions <name,array>
    """
    input_definition = definitions.copy()
    for parameter_name in parameter_dict.keys():
        parameter = parameter_dict[parameter_name]
        e = parameter.get_expression()
        if e is not None:

            value = e.evaluate_expression(input_definition)
            value = [value]
        else:

            value = evaluate_table(parameter.get_vector(), input_definition)

        parameter.set_value(value)
        input_definition[parameter_name] = parameter


def evaluate_table(list_values: list, definitions: dict) -> list:
    """
    evaluate_table function : evaluates a list of expression objects
    INPUT:  list_values -> list of expression objects
            definitions -> dictionary of definitions <name,value>
    OUTPUT: list <float>
    """

    all_values: list = []
    for value in list_values:

        value_i = value.get_name()
        if type(value_i) == Identifier:

            type_val = value_i.get_type()
            id_name = value_i.get_name()
            if not (id_name in definitions):

                error_('Undefined parameter : '+str(value_i))
            values = definitions[id_name]
            if type_val == "basic" and len(values) == 1:

                value_i = values[0]
            elif type_val == "basic" and len(values) > 1:

                error_('Parameter not properly defined : '+str(value_i))
            elif type_val == "assign":

                inner_expr = value_i.get_expression()
                index = inner_expr.evaluate_expression(definitions)
                if type(index) == float:

                    if index.is_integer() is False:

                        error_("Error: an index is a float: " + str(value_i))
                    index = int(round(index))

                if index < 0 or len(values) <= index:

                    error_('Parameter does not exit at this index : '+str(value_i))
                value_i = values[index]
        all_values.append(value_i)
    return all_values

#
# END Expression FUNCTIONS
#
