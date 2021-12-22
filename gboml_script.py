from compiler import parse_file, semantic, check_program_linearity, matrix_generation_a_b, matrix_generation_c, \
    factorize_program, extend_factor
from compiler.classes import Parameter, Expression, Node, Hyperlink, Time, Program
from compiler.utils import error_, move_to_directory
from enum import Enum
import os
from solver_api import cplex_solver, gurobi_solver, clp_solver
from copy import deepcopy
import numpy as np

# TODO
# first check the whole thing
# Structure and problem print
# Solve the whole thing
# Hyperedge problem ?


def test_gboml_python_interface():
    timehorizon_considered = 10
    model = GbomlGraph(timehorizon_considered)
    if model.get_timehorizon() != timehorizon_considered:
        error_('Timehorizon SET : FAILED')
    print("Timehorizon SET : OK ")

    model.set_timehorizon(12)
    if model.get_timehorizon() != 12:
        error_('Timehorizon CHANGE : FAILED')
    print("Timehorizon CHANGE : OK ")

    node_pv = model.import_node("examples/microgrid/microgrid.txt", "SOLAR_PV", copy=True)
    if node_pv.get_name() != "SOLAR_PV" and type(node_pv) != Node:
        error_('Import Node without renaming : FAILED')
    print("Import Node without renaming : OK")

    node_b = model.import_node("examples/microgrid/microgrid.txt", "A", new_node_name="B")
    if node_b.get_name() != "B" and type(node_b) != Node:
        error_('Import Node with renaming : FAILED')
    print("Import Node with renaming : OK")

    all_parameters_names = []
    all_parameters_values = []
    for i, parameter in enumerate(node_pv.get_parameters()):
        all_parameters_names.append(parameter.get_name())
        all_parameters_values.append(i)

    model.redefine_parameters_by_list(node_pv, all_parameters_names, all_parameters_values)
    for i, parameter in enumerate(node_pv.get_parameters_changes()):
        name = parameter.get_name()
        value = parameter.get_expression().get_name()

        if name != all_parameters_names[i] and value != all_parameters_values[i]:
            error_("Parameter change by list : FAILED")
    print("Parameter change by list : OK")
    node_pv_2 = model.import_node("examples/microgrid/microgrid.txt", "SOLAR_PV", copy=True)
    if len(node_pv_2.get_parameters_changes()) != 0:
        error_("Copying node : FAILED")
    print("Copying node : OK")

    model.remove_objective_in_node(node_pv_2, "hi")
    if len(node_pv_2.get_objectives()) != 0:
        error_("Removing objective : FAILED")
    print("Removing objective : OK")

    model.change_type_variable_in_node(node_pv_2, "investment", VariableType.EXTERNAL)
    if len(node_pv_2.get_variables_changes()) != 1:
        error_("Changing variables type : FAILED")

    var_name, var_type, line = node_pv_2.get_variables_changes()[0]
    if var_name != "investment" or var_type != VariableType.EXTERNAL.value:
        error_("Changing variables type : FAILED")
    print("Changing variables type : OK")

    model.add_node_in_model(node_b)

    model.build_model()
    print(model.solve_cplex())
    exit()


class VariableType(Enum):
    EXTERNAL = "external"
    INTERNAL = "internal"


class GbomlGraph():
    def __init__(self, timehorizon=1):
        self.list_nodes = []
        self.list_hyperedges = []
        self.timehorizon = Time("T", Expression('literal', timehorizon))
        self.node_hyperedge_dict = {}

        self.program = None
        self.matrix_a = None
        self.matrix_b = None
        self.vector_c = None
        self.indep_term_c = None
        self.factor_mapping = None
        self.objective_map = None

    def __add_node(self, to_add_node):
        node_name = to_add_node.get_name()
        if node_name in self.node_hyperedge_dict:
            error_("Reuse of same identifier twice for nodes or hyperedges : " + str(node_name))
        self.node_hyperedge_dict[node_name] = to_add_node
        self.list_nodes.append(to_add_node)

    def __add_hyperedge(self, to_add_hyperedge):
        hyperedge_name = to_add_hyperedge.get_name()
        if at_node is None:
            if hyperedge_name in self.node_hyperedge_dict:
                error_("Reuse of same identifier twice for nodes or hyperedges : " + str(hyperedge_name))
            self.node_hyperedge_dict[node_name] = to_add_hyperedge
            self.list_nodes.append(to_add_hyperedge)
        elif isinstance(at_node, Node):
            at_node.add_link(to_add_node)
            at_node.update_internal_dict()

    def __get__(self, *node_or_hyperedge_name, error=False, wanted_type=None):
        retrieved_object = None
        current_layer = self.node_hyperedge_dict
        depth_search = len(node_or_hyperedge_name)
        for i, name in enumerate(node_or_hyperedge_name):
            if name in current_layer:
                retrieved_object = current_layer[node_or_hyperedge_name]
                if i < depth_search-1 and isinstance(retrieved_object, Hyperlink):
                    error_("Hyperlinks do not possess subnodes or subhyperedges")
                elif i < depth_search-1:
                    current_layer = retrieved_object.get_internal_dict()

            elif error:
                error_("Unknown node or hyperedge named " + str(node_or_hyperedge_name))

        if wanted_type and not isinstance(retrieved_object, wanted_type):
            error_("Error wanted type " + str(wanted_type) + " but that name references a " +
                   str(type(retrieved_object)))

        return retrieved_object

    def add_node_in_model(self, *nodes: Node):
        for node in nodes:
            self.__add_node(node)

    def add_hyperedges_in_model(self, *hyperedges: Hyperlink):
        for hyperedge in hyperedges:
            self.__add_hyperedge(hyperedge)

    def set_timehorizon(self, value):
        self.timehorizon = Time("T", Expression('literal', value))

    def get_timehorizon(self):
        return self.timehorizon.get_value()

    def build_model(self, nb_processes: int = 1):
        program = Program(self.list_nodes, timescale=self.timehorizon, links=self.list_hyperedges)
        program, program_variables_dict, definitions = semantic(program)
        check_program_linearity(program, program_variables_dict, definitions)
        factorize_program(program, program_variables_dict, definitions)
        if nb_processes > 1:
            extend_factor_on_multiple_processes(program, definitions, nb_processes)
        else:
            extend_factor(program, definitions)

        matrix_a, vector_b, factor_mapping = matrix_generation_a_b(program)
        vector_c, indep_terms_c, objective_map = matrix_generation_c(program)
        program.free_factors_objectives()

        self.program = program
        self.matrix_a = matrix_a
        self.matrix_b = vector_b
        self.vector_c = vector_c
        self.indep_term_c = indep_terms_c
        self.factor_mapping = factor_mapping
        self.objective_map = objective_map

    def __solve(self, solver_function):
        vector_c = np.asarray(self.vector_c.sum(axis=0), dtype=float)
        objective_offset = float(self.indep_term_c.sum())
        return solver_function(self.matrix_a, self.matrix_b, vector_c, objective_offset, self.program.get_tuple_name())

    def solve_cplex(self):
        return self.__solve(cplex_solver)

    def solve_gurobi(self):
        return self.__solve(gurobi_solver)

    def solve_clp(self):
        return self.__solve(clp_solver)

    @staticmethod
    def import_all_nodes_and_edges(filename):
        old_dir, cut_filename = move_to_directory(filename)
        filename_graph = parse_file(cut_filename)
        all_nodes = filename_graph.get_nodes()
        all_hyperedges = filename_graph.get_links()
        os.chdir(old_dir)
        return all_nodes, all_hyperedges

    @staticmethod
    def import_node(filename: str, *imported_node_identifier: str, new_node_name: str = "", copy=False):
        old_dir, cut_filename = move_to_directory(filename)
        filename_graph = parse_file(cut_filename)
        print("salut ", imported_node_identifier)
        imported_node = filename_graph.get(imported_node_identifier)

        if imported_node is None:
            error_("ERROR: In file " + str(filename) + " there is no node named " + str(imported_node_identifier))

        if type(imported_node) != Node:
            error_("ERROR: A node named " + str(imported_node_identifier) + " is imported as type hyperedge ")

        if new_node_name == "":
            new_node_name = imported_node_identifier[-1]

        if copy:
            imported_node = deepcopy(imported_node)

        imported_node.rename(new_node_name)
        os.chdir(old_dir)
        return imported_node

    @staticmethod
    def import_hyperedge(filename: str, *imported_hyperedge_identifier: str,
                         new_hyperedge_name: str = ""):
        old_dir, cut_filename = move_to_directory(filename)
        filename_graph = parse_file(filename)
        imported_hyperedge = filename_graph.get(imported_hyperedge_identifier)

        if imported_hyperedge is None:
            error_("ERROR: In file " + str(filename) + " there is no node named " + str(imported_hyperedge_identifier))

        if type(imported_hyperedge) == Hyperlink:
            error_("ERROR: A hyperedge named " + imported_node_identifier + " is imported as type node ")

        if new_hyperedge_name == "":
            new_hyperedge_name = imported_hyperedge_identifier[-1]

        if copy:
            imported_hyperedge = deepcopy(imported_hyperedge)

        imported_hyperedge.rename(new_hyperedge_name)
        os.chdir(old_dir)
        return imported_hyperedge

    @staticmethod
    def rename(node_or_hyperedge, new_name):
        node_or_hyperedge.rename(new_name)

    @staticmethod
    def get_inside_node(at_node, *searched_node: str, wanted_type=None):
        current_layer = at_node.get_internal_dict()
        depth_search = len(searched_node)
        retrieved_object = None
        for i, name in enumerate(searched_node):
            if name in current_layer:
                retrieved_object = current_layer[name]
                if i < depth_search - 1 and isinstance(retrieved_object, Hyperlink):
                    error_("Hyperlinks do not possess subnodes or subhyperedges")
                elif i < depth_search - 1:
                    current_layer = retrieved_object.get_internal_dict()

            elif error:
                error_("Unknown node or hyperedge named " + str(node_or_hyperedge_name))

        if wanted_type and not isinstance(retrieved_object, wanted_type):
            error_("Error wanted type " + str(wanted_type) + " but that name references a " +
                   str(type(retrieved_object)))

        return retrieved_object

    @staticmethod
    def add_sub_node(node_to_add: Node, at_node: Node):
        at_node.add_sub_node(node_to_add)
        at_node.update_internal_dict()

    @staticmethod
    def add_sub_hyperedge(hyperedge_to_add: Hyperlink, at_node: Node):
        at_node.add_link(hyperedge_to_add)
        at_node.update_internal_dict()

    @staticmethod
    def redefine_parameter_with_value(node_or_hyperedge, parameter_name: str, value: float):
        expr = Expression('literal', value)
        parameter = Parameter(parameter_name, expr)
        print(parameter)
        node_or_hyperedge.add_parameter_change(parameter)

    @staticmethod
    def redefine_parameter_with_values(node_or_hyperedge, parameter_name: str, values: list):
        expression_values = []
        for value in values:
            expr = Expression('literal', value)
            expression_values.append(expr)
        parameter = Parameter(parameter_name, None)
        parameter.set_vector(expression_values)
        node_or_hyperedge.add_parameter_change(parameter)

    @staticmethod
    def redefine_parameter_with_file_import(node_or_hyperedge, parameter_name: str, filename):
        parameter = Parameter(parameter_name, filename)
        node_or_hyperedge.add_parameter_change(parameter)

    @staticmethod
    def redefine_parameters_by_list(node_or_hyperedge, list_parameters: list = [], list_values: list = []):
        assert len(list_parameters) == len(list_values), "Unmatching size between list or parameters and list of values"
        for i in range(len(list_parameters)):
            parameter_name = list_parameters[i]
            value = list_values[i]
            if isinstance(value, str):
                GbomlGraph.redefine_parameter_with_file_import(node_or_hyperedge, parameter_name, value)
            elif isinstance(value, float) or isinstance(value, int):
                GbomlGraph.redefine_parameter_with_value(node_or_hyperedge, parameter_name, value)
            elif isinstance(value, list):
                GbomlGraph.redefine_parameter_with_values(node_or_hyperedge, parameter_name, value)
            else:
                error_("Unaccepted type value for parameter redefiniton "+str(type(value)))

    @staticmethod
    def redefine_parameters(node_or_hyperedge, **kwargs):
        for parameter_name, value in kwargs.items():
            if isinstance(value, str):
                GbomlGraph.redefine_parameter_with_file_import(node_or_hyperedge, parameter_name, value)
            elif isinstance(value, float) or isinstance(value, int):
                GbomlGraph.redefine_parameter_with_value(node_or_hyperedge, parameter_name, value)
            elif isinstance(value, list):
                GbomlGraph.redefine_parameter_with_values(node_or_hyperedge, parameter_name, value)
            else:
                error_("Unaccepted type value for parameter redefiniton " + str(type(value)))

    @staticmethod
    def change_type_variable_in_node(node: Node, variable_name: str, variable_type: VariableType):
        print(variable_type.value)
        variable_tuple = [variable_name, variable_type.value, 0]
        node.add_variable_change(variable_tuple)

    @staticmethod
    def remove_constraint(node_or_hyperedge: Node, *to_delete_constraints_names):
        constraints = node_or_hyperedge.get_constraints()
        to_delete_constraints_names = list(to_delete_constraints_names)
        for constraint in constraints:
            constraint_name = constraint.get_name()
            if constraint_name in to_delete_constraints_names:
                node_or_hyperedge.remove_constraint(constraint)
                to_delete_constraints_names.remove(constraint_name)

        if to_delete_constraints_names:
            error_("Could not delete "+str(to_delete_constraints_names)+" as they were not found in "
                   + str(node_or_hyperedge.get_name()))

    @staticmethod
    def remove_objective_in_node(node: Node, *to_delete_objectives_names):
        objectives = node.get_objectives()
        to_delete_objectives_names = list(to_delete_objectives_names)
        for objective in objectives:
            objective_name = objective.get_name()
            if objective_name in to_delete_objectives_names:
                node.remove_objective(objective)
                to_delete_objectives_names.remove(objective_name)

        if to_delete_objectives_names:
            error_("Could not delete " + str(to_delete_objectives_names) + " as they were not found in hyperedge "
                   + str(node.get_name()))

    @staticmethod
    def change_node_name_in_hyperedge(hyperedge: Hyperlink, old_node_name, new_node_name):
        change_tuple = [old_node_name, new_node_name, None]
        hyperedge.add_name_change(change_tuple)


test_gboml_python_interface()

model = GbomlGraph(1)

print(model.import_all_nodes_and_edges("examples/microgrid/microgrid.txt"))
returned_node = model.import_node("examples/microgrid/microgrid.txt", "A", new_node_name="B", copy=True)
model.change_type_variable_in_node(returned_node, 'x', VariableType.EXTERNAL)
model.add_node_in_model(returned_node)
model.build_model()
exit()

model.redefine_parameters(returned_node, a=2)
print(returned_node)
model.add_node_in_model(returned_node)
pv = model.import_node("examples/microgrid/microgrid.txt", "SOLAR_PV")
bo = model.get_inside_node(pv, "bae", "bo", wanted_type=Node)
print(bo)
model.build_model(1)

exit()
