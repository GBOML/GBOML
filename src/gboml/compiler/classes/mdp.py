# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).

from .expression import Expression


class State:

    def __init__(self, name: str, node_name: str,
                 dynamic: Expression, initial: Expression):
        self.node_name = node_name
        self.name = name
        self.dynamic = dynamic
        self.initial = initial

    def get_node_name(self) -> str:

        return self.node_name

    def get_name(self) -> str:

        return self.name

    def get_dynamic(self) -> Expression:

        return self.dynamic

    def get_init(self) -> Expression:

        return self.initial


class Action:

    def __init__(self, name: str, node_name: str,
                 lower_bound: Expression, upper_bound: Expression):
        self.name = name
        self.node_name = node_name
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def get_node_name(self) -> str:

        return self.node_name

    def get_name(self) -> str:

        return self.name

    def get_lower_bound(self) -> Expression:

        return self.lower_bound

    def get_upper_bound(self) -> Expression:

        return self.upper_bound


class Sizing(Action):

    def __init__(self, name: str, node_name: str,
                 lower_bound: Expression, upper_bound: Expression):

        Action.__init__(self, name, node_name, lower_bound, upper_bound)


class Auxiliary:

    def __init__(self, name: str, node_name: str, definition: Expression):
        self.name = name
        self.node_name = node_name
        self.definition = definition

    def get_name(self) -> str:

        return self.name

    def get_definition(self) -> Expression:

        return self.definition


class MDPObjective:
    def __init__(self, node_name: str, expression: Expression):
        self.node_name = node_name
        self.expression = expression

    def get_node_name(self):
        return self.node_name

    def get_expression(self):
        return self.expression


class MDP:

    def __init__(self, states: list, actions: list,
                 sizing: list, auxiliaries: list, objectives: list):

        # states -> list of State objects
        # actions -> list of Action objects
        # sizing -> list of Sizing objects
        # auxiliaries -> list of Auxiliary objects

        self.sizing = sizing
        self.states = states
        self.actions = actions
        self.auxiliaries = auxiliaries
        self.objectives = objectives

    def get_objectives(self) -> list:
        return self.objectives

    def get_states_variables(self) -> list:

        return self.states

    def get_auxiliary_variables(self) -> list:

        return self.auxiliaries

    def get_sizing_variables(self) -> list:

        return self.sizing

    def get_actions_variables(self) -> list:

        return self.actions
