from gboml import GbomlGraph
import gboml.compiler.classes as gcc

import json
import os
import sys
from datetime import datetime
import argparse

def pipe_and_or_boat(nodes, edges, constraint="pipe_and_boat"):
    """
    Remove PIPE_CO2, PIPE_CO2_GR or CARRIER_CO2, CARRIER_CO2_GR from the edges and nodes.
    
    Select constraints in:
    PIPE_CO2_CONNECTION
    COASTAL_CARBON_DIOXIDE_BALANCE
    COASTAL_CARBON_DIOXIDE_BALANCE_GR
    
    Parameters
    ----------
    edges : list
        List of edges
    nodes : list
        List of nodes
    constraint : str
        Str to choose between ["pipe_and_boat", "only_carrier", "only_pipe"]
    
    Returns
    -------
    edges : list
        New list of edges
    nodes : list
        New list of nodes
    """
    ls_edges = ["PIPE_CO2_CONNECTION", "COASTAL_CARBON_DIOXIDE_BALANCE", 
                "COASTAL_CARBON_DIOXIDE_BALANCE_GR", "POWER_LINE", 
                "COASTAL_LIQUEFIED_METHANE_BALANCE_GR", "COASTAL_LIQUEFIED_METHANE_BALANCE"]
    
    constraints = ["pipe_and_boat", "only_carrier", "only_pipe"]

    assert constraint in constraints
    constraints.remove(constraint)

    if constraint == "pipe_and_boat":
        ls_nodes = []
    elif constraint == "only_carrier":
        ls_nodes = ["PIPE_CO2", "PIPE_CO2_GR"]
    elif constraint == "only_pipe":
        ls_nodes = ["CARRIER_CO2", "CARRIER_CO2_GR"]

    for e in edges:
        
        if e.name in ls_edges:
            # print(e.name)
            e.constraints = list(filter(lambda x: x.name not in constraints, e.constraints))


    nodes = list(filter(lambda x: x.name not in ls_nodes, nodes))
    
    return edges, nodes

def remove_cap(edges):
    """
    Remove cap CO2 from edges
    
    Parameters
    ----------
    edges : list
        List of edges
        
    Returns
    -------
    edges : list
        New edges
    """
    edges = list(filter(lambda x: x.name != "CAP_CO2", edges))
    return edges

def cap(param, cap_co2):
    """
    Update cap_co2 parameter
    
    Parameters
    ----------
    param : list
        List of parameters
    cap_co2 : float
        value of cap_co2
        
    Returns
    -------
    param : list
        New list of parameters
    """
    param = list(filter(lambda x: x.name != "cap_co2", param))
    param.append(gcc.Parameter("cap_co2", 
                            gcc.Expression("literal", cap_co2)))

    return param

def emission_cost(param, co2_emission_cost):
    """
    Update co2_emission_cost parameter
    
    Parameters
    ----------
    param : list
        List of parameters
    co2_emission_cost : float
        value of co2_emission_cost
        
    Returns
    -------
    param : list
        New list of parameters
    """
    param = list(filter(lambda x: x.name != "co2_emission_cost", param))
    param.append(gcc.Parameter("co2_emission_cost", 
                            gcc.Expression("literal", co2_emission_cost)))

    return param

def set_ens_cost(param, e_ens_cost):
    """
    Update e_ens_cost parameter
    
    Parameters
    ----------
    param : list
        List of parameters
    e_ens_cost : float
        value of e_ens_cost
        
    Returns
    -------
    param : list
        New list of parameters
    """
    param = list(filter(lambda x: x.name != "e_ens_cost" , param))
    param.append(gcc.Parameter("e_ens_cost", 
                            gcc.Expression("literal", e_ens_cost)))

    return param

def ens_allowed(nodes):
    """
    Remove ens==0 from ENERGY_DEMAND_BE nodes constraints
    
    Parameters
    ----------
    nodes : list
        List of nodes
        
    Returns
    -------
    nodes : list
        New list of nodes
    """
    for n in nodes:
        if n.name == "ENERGY_DEMAND_BE":
            for c in n.constraints:
                if c.get_name() == "dual_constraint":
                    n.constraints.remove(c)

    return nodes

# if needed use click to be able to change the arguments of the main and the configuration.
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', help='Name gboml file',
                        type=str, default="multi_hub")
    parser.add_argument('-y', '--years', help='Number of years',
                        type=int, default=3)
    parser.add_argument('-c', '--cap_co2', help="Cap on CO2 if None no cap on CO2",
                        type=float, default=0.0)
    parser.add_argument('-cost_co2', '--co2_emission_cost', help="Cost on CO2 in M€/kt",
                        type=float, default=80*10**(-3))
    parser.add_argument('-ens', '--e_ens_cost', help="Cost on ens in M€/GWh",
                        type=float, default=3.)
    parser.add_argument('-sc', '--scenario', help="Number of scenrio",
                        type=int, default=0)
    parser.add_argument('-p_c', "--pipe_carrier", help="Select constraint",
                        choices=["pipe_and_boat", "only_carrier", "only_pipe"],
                        default="pipe_and_boat")
    args = parser.parse_args()

    name = args.name
    years = args.years
    cap_co2 = args.cap_co2
    co2_emission_cost = args.co2_emission_cost
    e_ens_cost = args.e_ens_cost
    scenario = args.scenario
    constraint = args.pipe_carrier
    ens_permitted = False
    
    timehorizon = 24*365*years



    gboml_model = GbomlGraph(timehorizon=timehorizon)
    nodes, edges, param = gboml_model.import_all_nodes_and_edges(args.name + ".gboml")

    if args.scenario == 1: # Scenario with cap on CO2, No ens and Carrier
        co2_emission_cost = 0
        constraint="only_carrier"

    elif args.scenario == 2: # Sc with CAP on CO2, ENS , Carrier
        co2_emission_cost = 0

        # Remove constraint ENS == 0
        e_ens_cost = 3
        nodes = ens_allowed(nodes=nodes)
        param = set_ens_cost(param=param, e_ens_cost=e_ens_cost)
        ens_permitted = True

        constraint="only_carrier"


    elif args.scenario == 3: # Scenario with no cap, ens, with a cost for CO2 0.08
        # Remove cap_co2 hyperedge
        edges = remove_cap(edges)
        cap_co2 = None

        # Remove constraint ENS == 0
        e_ens_cost = 3
        nodes = ens_allowed(nodes=nodes)
        param = set_ens_cost(param=param, e_ens_cost=e_ens_cost)
        ens_permitted = True

        # Set an emission cost
        co2_emission_cost = 0.08
        param = emission_cost(param=param, co2_emission_cost=co2_emission_cost)
        
        constraint="only_carrier"

    elif args.scenario == 4: # With no cap, with ens, without cost for co2
        # Remove cap_co2 hyperedge
        edges = remove_cap(edges)
        cap_co2 = None

        # Remove constraint ENS == 0
        e_ens_cost = 3
        nodes = ens_allowed(nodes=nodes)
        param = set_ens_cost(param=param, e_ens_cost=e_ens_cost)
        ens_permitted = True

        # Set an emission cost
        co2_emission_cost = 0.0
        param = emission_cost(param=param, co2_emission_cost=co2_emission_cost)
        
        constraint="only_carrier"

    elif scenario == 5: # Scenario 1 but with Greenlandpython3 
        co2_emission_cost = 0

        nodes, edges, param = gboml_model.import_all_nodes_and_edges("greenland.gboml")

        constraint="only_carrier"

    elif scenario == 6:
        # Remove cap_co2 hyperedge
        edges = remove_cap(edges)
        cap_co2 = None

        # Set an emission cost
        co2_emission_cost = 0.0
        param = emission_cost(param=param, co2_emission_cost=co2_emission_cost)
        
        constraint="only_carrier"

    else:
        co2_emission_cost = 0
        constraint="only_carrier"


    # Boat or pipe This line is needed otherwise too many constraints
    edges, nodes = pipe_and_or_boat(nodes=nodes, edges=edges, constraint=constraint)

    gboml_model.add_global_parameters(param)
    gboml_model.add_nodes_in_model(*nodes)
    gboml_model.add_hyperedges_in_model(*edges)
    gboml_model.build_model()
    solution, obj, status, solver_info, constr_info, _ = gboml_model.solve_gurobi("options.opt", details="details.txt")
    print("Solved")
    gathered_data = gboml_model.turn_solution_to_dictionary(solver_info, status, solution, obj, constr_info)
    print("Json done")
  
    if not os.path.exists("Results"):
        os.makedirs("Results")

    with open(f'Results/sc_{args.scenario}_T_{timehorizon}_cap_co2_{cap_co2}_costco2_{co2_emission_cost}_ensAllowed_{ens_permitted}_costens_{args.e_ens_cost}_{constraint}.json', "w") as fp:
        json.dump(gathered_data, fp, indent=4)
