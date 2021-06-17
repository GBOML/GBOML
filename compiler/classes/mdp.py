
from compiler.classes.expression import Expression


class State:

    def __init__(self, name: str, dynamic: Expression, initial: Expression):
        self.name = name
        self.dynamic = dynamic
        self.initial = initial

    def get_name(self) -> str:

        return self.name

    def get_dynamic(self) -> Expression:

        return self.dynamic

    def get_init(self) -> Expression:

        return self.initial


class Sizing:

    def __init__(self, name: str):

        self.name = name

    def get_name(self) -> str:

        return self.name


class Action:

    def __init__(self, name: str, lower_bound: Expression, upper_bound: Expression):
        self.name = name
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def get_name(self) -> str:

        return self.name

    def get_lower_bound(self) -> Expression:

        return self.lower_bound

    def get_upper_bound(self) -> Expression:

        return self.upper_bound


class Auxiliary:

    def __init__(self, name: str, definition: Expression):
        self.name = name
        self.definition = definition

    def get_name(self) -> str:

        return self.name

    def get_defintion(self) -> Expression:

        return self.definition


class MDP:

    def __init__(self, states: list, actions: list, sizing: list, auxiliaries: list):

        # states -> list of State objects
        # actions -> list of Action objects
        # sizing -> list of Sizing objects
        # auxiliaries -> list of Auxiliary objects

        self.sizing = sizing
        self.states = states
        self.actions = actions
        self.auxiliaries = auxiliaries

    def get_states_variables(self) -> list:

        return self.states

    def get_auxiliary_variables(self) -> list:

        return self.auxiliaries

    def get_sizing_variables(self) -> list:

        return self.sizing

    def get_actions_variables(self) -> list:

        return self.actions
