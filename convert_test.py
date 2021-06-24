from convert import convert_mdp

from compiler.classes.expression import Expression
from compiler.classes.identifier import Identifier
from compiler.classes.link import Attribute
from compiler.classes.mdp import MDP, State, Action, Auxiliary, Sizing, MDPObjective

if __name__ == '__main__':

    dynamic_expr = Expression('+')
    dynamic_expr.add_child(Expression('literal', Attribute('node', Identifier('basic', 'expr_state'))))
    dynamic_expr.add_child(Expression('literal', Attribute('node', Identifier('basic', 'expr_action'))))
    initial_expr = Expression('literal', 0.0)
    state = State('expr_state', 'node', dynamic_expr, initial_expr)

    lower_expr = Expression('literal', 0.0)
    upper_expr = Expression('literal', 1.0)
    action = Action('expr_action', 'node', lower_expr, upper_expr)

    objective_expr = Expression('literal', Attribute('node', Identifier('basic', 'expr_state')))
    objective = MDPObjective('node', objective_expr)

    mdp = MDP(states=[state], actions=[action], sizing=[], auxiliaries=[], objectives=[objective])
    convert_mdp(mdp)
