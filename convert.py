from compiler import parameter_evaluation, check_names_repetitions, match_dictionaries
from compiler.classes import Program
# TODO: recheck required imports
from compiler.classes.mdp import MDP, State, Action, Auxiliary, Sizing

import json

def convert_mdp(mdp:MDP):
    states = mdp.get_states_variables()
    nb_states = len(states)
    actions = mdp.get_actions_variables()
    nb_actions = len(actions)

    # Build definitions dictionary
    # TODO: get parameter values and add to dictionary
    # TODO: adjust variable names for functions besides dynamics()
    definitions = {}
    for i in range(nb_states):
        definitions[states[i].get_name()] = ['previous_states[..., ' + str(i) +']']

    for i in range(nb_actions):
        definitions[actions[i].get_name()] = ['actions[..., ' + str(i) +']']

    # TODO: clamp actions to their bounds (vectorize if possible)
    tabs = '        '
    dynamics_body = tabs + 'states = torch.empty(previous_states.size())\n'
    for i in range(nb_states):
        dynamics_body += tabs + 'states[...,' + str(i) + '] = ' \
            + states[i].get_dynamic().evaluate_python_string(definitions) + '\n'

    initial_body = tabs + 'states = torch.empty((number_trajectories, ' + str(nb_states) + '))\n'
    for i in range(nb_states):
        initial_body += tabs + 'states[...,' + str(i) + '] = ' \
            + states[i].get_init().evaluate_python_string(definitions) + '\n'

    # Write python source file
    filename = 'convert/GBOMLSystem.py'

    print('Writing DESGA system to file "' + filename + '"')
    with open(filename, 'w') as outfile:
        # imports
        outfile.write('import torch\n')
        outfile.write('from system.GBOMLSystem import GBOMLBaseSystem\n')

        # class header
        outfile.write('\n')
        outfile.write('class GBOMLSystem(GBOMLBaseSystem.GBOMLBaseSystem):\n')

        # dynamics function
        outfile.write('\n')
        outfile.write('    def dynamics(self, previous_states, actions, disturbances):\n')
        outfile.write(dynamics_body)
        outfile.write('        return states\n')

        # initial_state function
        outfile.write('\n')
        outfile.write('    def initial_state(self, number_trajectories=1):\n')
        outfile.write(initial_body)
        outfile.write('        return states\n')

        # reward function
        outfile.write('\n')
        outfile.write('    def reward(self, states, actions, disturbances):\n')
        outfile.write('        return states + self.parameters[0] - self.parameters[0]\n')

def convert_simulation(program:Program):
    print('Converting input to DESGA format')
    write_system(program)
    write_config(program)

def write_system(program:Program):
    parameter_map = program.get_dict_global_parameters()
    # NOTE: retrieval of global parameter values copied from semantic(program:Program) function

    #Retrieve time horizon
    time = program.get_time()
    time.check()
    time_value = time.get_value()
    
    #Check if all nodes have different names
    node_list = program.get_nodes()
    check_names_repetitions(node_list)

    #Check if an objective function is defined
    program.check_objective_existence()

    definitions = {}
    definitions["T"]=[time_value]

    global_param = program.get_global_parameters()
    global_definitions = parameter_evaluation(global_param,definitions.copy())
    global_definitions.pop("T") # TODO: what is this for?
    definitions["global"]= global_definitions
    definitions["GLOBAL"]= global_definitions

    # NOTE: end of copy from semantic(program:Program) function

    for node in program.get_nodes():

        if node.get_name() != 'system':
            print('Skipping node ' + node.get_name())
            continue
        else:
            print('Exploring node "' + node.get_name() + '"')

        # Build a dictionary with the locally appropriate values for parameters and variables.
        # Dictionary layout:
        # "global" -> dictionary
        #             name -> value
        # local name -> value
        # All values are given as lists (of length 1 for scalars)
        # - Parameter values can be strings, floats, or integers (all will be converted to string by evaluate_python_string())
        # - Variable values must be given as strings (numerical values unknown)

        #Initialize dictionary of defined parameters
        parameter_dictionary = definitions.copy()

        #Retrieve all the parameters'names in set
        node_parameters = node.get_dictionary_parameters() 

        #Retrieve a dictionary of [name,identifier object] tuple
        node_variables = node.get_dictionary_variables()

        #Check if variables and parameters share names
        match_dictionaries(node_parameters,node_variables)

        #Add evaluated parameters to the dictionary of defined paramaters
        parameter_dictionary = parameter_evaluation(node.get_parameters(),parameter_dictionary)


        # Check for expected structure in known test file
        if len(node_variables) != 2:
            print('WARNING: number of node variables unexpected')

        for name in ['states', 'actions']:
            if not name in node_variables:
                print('WARNING: no node variable called "' + name + '"')
            elif node_variables[name].size != 1:
                print('WARNING: variable "' + name + '" is not a scalar')

        # Define translation for expected variables
        parameter_dictionary['states'] = ['previous_states']
        parameter_dictionary['actions'] = ['actions']

        # Translate first objective as stand-in for dynamics
        obj = node.get_objectives()[0]
        dynamics = obj.get_expression().evaluate_python_string(parameter_dictionary)

    # Write python source file
    filename = 'convert/GBOMLSystem.py'

    print('Writing DESGA system to file "' + filename + '"')
    with open(filename, 'w') as outfile:
        # imports
        outfile.write('import torch\n')
        outfile.write('from system.GBOMLSystem import GBOMLBaseSystem\n')

        # class header
        outfile.write('\n')
        outfile.write('class GBOMLSystem(GBOMLBaseSystem.GBOMLBaseSystem):\n')

        # dynamics function
        outfile.write('\n')
        outfile.write('    def dynamics(self, previous_states, actions, disturbances):\n')
        outfile.write('        return ' + dynamics + '\n')

        # initial_state function
        outfile.write('\n')
        outfile.write('    def initial_state(self, number_trajectories=1):\n')
        outfile.write('        return torch.zeros((number_trajectories, 1), device=self.device)\n')

        # reward function
        outfile.write('\n')
        outfile.write('    def reward(self, states, actions, disturbances):\n')
        outfile.write('        return states + self.parameters[0] - self.parameters[0]\n')

def write_config(program:Program):
    #Retrieve time horizon
    time = program.get_time()
    time.check()
    time_value = time.get_value()

    # Write DESGA config file
    filename = 'convert/gboml-desga.json'

    config_dict = {}

    system_dict = {}
    system_dict['name'] = 'GBOMLSystem'
    system_dict['init'] = {}
    system_dict['init']['horizon'] = time_value
    system_dict['init']['feasible_set'] = {}
    system_dict['init']['feasible_set']['gen'] = [0,0.1]
    system_dict['wrappers'] = {}
    config_dict['system'] = system_dict

    agent_dict = {}
    agent_dict['name'] = 'DSSAAgent'
    agent_dict['init'] = {}
    agent_dict['init']['InvestmentModel'] = 'DeterministicParameterModel'
    agent_dict['init']['OperationModel'] = 'GaussianDistModel'
    agent_dict['initialize'] = {}
    agent_dict['initialize']['investment_pol'] = {}
    agent_dict['initialize']['operation_pol'] = {}
    agent_dict['initialize']['operation_pol']['layers'] = [64]
    config_dict['agent'] = agent_dict

    experiment_dict = {}
    experiment_dict['seed'] = {}
    experiment_dict['seed']['value'] = 1234
    experiment_dict['fit'] = {}
    experiment_dict['fit']['path'] = {}
    experiment_dict['fit']['path']['logdir'] = './experiments'
    experiment_dict['fit']['path']['model_name'] = 'gboml-env'
    experiment_dict['fit']['logger'] = {}
    experiment_dict['fit']['logger']['name'] = 'LoggerDESGA'
    experiment_dict['fit']['logger']['init'] = {}
    experiment_dict['fit']['algo'] = {}
    experiment_dict['fit']['algo']['name'] = 'ReinforceDESGA'
    experiment_dict['fit']['algo']['init'] = {}
    experiment_dict['fit']['algo']['initialize'] = {}
    experiment_dict['fit']['algo']['initialize']['nb_iterations'] = 150
    experiment_dict['fit']['algo']['initialize']['optimizer_parameters'] = {}
    experiment_dict['fit']['algo']['initialize']['optimizer_parameters']['lr'] = 0.001
    experiment_dict['fit']['algo']['initialize']['batch_size'] = 64
    experiment_dict['fit']['algo']['initialize']['mc_samples'] = 100
    experiment_dict['fit']['algo']['initialize']['system_fit'] = True
    experiment_dict['fit']['save_agent'] = True
    experiment_dict['simulate'] = {}
    experiment_dict['simulate']['runner'] = {}
    experiment_dict['simulate']['runner']['name'] = 'TrajectoriesSampler'
    experiment_dict['simulate']['runner']['init'] = {}
    experiment_dict['simulate']['nb_simulations'] = 100
    config_dict['experiment'] = experiment_dict

    print('Writing DESGA config to file "' + filename + '"')
    with open(filename, 'w') as outfile:
        json.dump(config_dict, outfile,indent=4)
