from convert import convert_mdp

from compiler.classes.expression import Expression
from compiler.classes.identifier import Identifier
from compiler.classes.link import Attribute
from compiler.classes.mdp import MDP, State, Action, Auxiliary, Sizing

if __name__ == '__main__':

    dynamic = Expression('+')
    dynamic.add_child(Expression('literal', Attribute('node', Identifier('basic', 'expr_state'))))
    dynamic.add_child(Expression('literal', Attribute('node', Identifier('basic', 'expr_action'))))
    initial = Expression('literal', 0.0)
    state = State('expr_state', 'node', dynamic, initial)

    lower = Expression('literal', 0.0)
    upper = Expression('literal', 1.0)
    action = Action('expr_action', 'node', lower, upper)

    mdp = MDP(states=[state], actions=[action], sizing=[], auxiliaries=[], objectives=[])
    convert_mdp(mdp)
