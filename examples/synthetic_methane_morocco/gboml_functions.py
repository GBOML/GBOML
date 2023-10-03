
from gboml import GbomlGraph
import gboml.compiler.classes as gcc
import json
import os


def main(file_name, timehorizon, methane_demand, hydrogen_demand, water_demand, co2_demand, scenario, renewable_energy):
    
    """ GBOML graph run """
    
    statut, output_file = gboml_graph_run_and_alteration(file_name, timehorizon, methane_demand, hydrogen_demand, water_demand, co2_demand, scenario)
    if statut != 0:
        if hydrogen_demand != 0:
            commodity = 'hydrogen'
        elif water_demand != 0:
            commodity = 'water'
        elif co2_demand != 0 and scenario == 1:
            commodity = 'co2_s1'
        elif co2_demand != 0 and scenario == 2:
            commodity = 'co2_s2'
        elif co2_demand != 0 and scenario == 3:
            commodity = 'co2_s3'
        else:
            exit()  
        
        """ Cost calculation """
            
        commodity_price(output_file, commodity, renewable_energy)
        
    else:
        exit()
        
    return

        
def gboml_graph_run(file_name, timehorizon):
    
    """ GBOML graph creation and running """
    file_name = os.path.splitext(file_name)[0]
    
    gboml_model = GbomlGraph(timehorizon=timehorizon)
    nodes, edges, global_param = gboml_model.import_all_nodes_and_edges(file_name + '.txt')
    gboml_model.add_global_parameters(global_param)
    gboml_model.add_nodes_in_model(*nodes)
    gboml_model.add_hyperedges_in_model(*edges)
    gboml_model.build_model()
    solution, obj, status, solver_info, constr_info, _ = gboml_model.solve_gurobi()
    print("Solved")
    gathered_data = gboml_model.turn_solution_to_dictionary(solver_info, status, solution, obj, constr_info)
    
    out_dir = 'model_outputs'
    os.makedirs(out_dir, exist_ok=True)
    scenario_nbre = os.path.split(file_name)[-1]
    out_file = os.path.join(out_dir, scenario_nbre)
    
    with open(out_file + '.json', "w") as fp:
        json.dump(gathered_data, fp, indent=4)
    
    print(out_file + '.json saved')
    
    return
        

def gboml_graph_run_and_alteration(file_name, timehorizon, methane_demand, hydrogen_demand, water_demand, co2_demand, scenario): 
    # return statut, output_file
    # statut = 0 in case of error
    
    file_name = os.path.splitext(file_name)[0]
    demand_list = [methane_demand, hydrogen_demand, water_demand, co2_demand]
    nb_commodity_different_zero = 0
    for i in demand_list:
        if i != 0:
            nb_commodity_different_zero += 1
            if nb_commodity_different_zero > 1:
                print("TypeError: There must be only one commodity demand")
                return 0, ''
        
        
    """ GBOML graph creation """           
                
    gboml_model = GbomlGraph(timehorizon=timehorizon)
    nodes, edges, global_param = gboml_model.import_all_nodes_and_edges(file_name + '.txt')
    
    
    """ GBOML graph alteration """
    
    for e in edges:
        if e.name == 'WATER_BALANCE_HUB':
            e.parameters = list(filter(lambda x: x.name != "demand" , e.parameters))
            e.parameters.append(gcc.Parameter('demand', gcc.Expression('literal', water_demand)))
                
        if e.name == 'HYDROGEN_BALANCE_HUB':
            e.parameters = list(filter(lambda x: x.name != "demand" , e.parameters))
            e.parameters.append(gcc.Parameter('demand', gcc.Expression('literal', hydrogen_demand)))
            
                  
        if e.name == 'METHANE_BALANCE_DESTINATION':
            e.parameters = list(filter(lambda x: x.name != "demand" , e.parameters))
            e.parameters.append(gcc.Parameter('demand', gcc.Expression('literal', methane_demand)))
               
        if e.name == 'CO2_BALANCE_HUB':
            e.parameters = list(filter(lambda x: x.name != "demand" , e.parameters))
            e.parameters.append(gcc.Parameter('demand', gcc.Expression('literal', co2_demand)))
            
        if scenario == 3 and e.name == 'CO2_PROD_DESTINATION':
            conversion_factor_methane = e.parameters[1].expression.evaluate_expression({})  # kt CH4 / kt CO2
            e.parameters = list(filter(lambda x: x.name != "demand" , e.parameters))
            e.parameters.append(gcc.Parameter('demand', gcc.Expression('literal', co2_demand * conversion_factor_methane)))
        
              
    """ GBOML graph run with gurobi """
    
    gboml_model.add_global_parameters(global_param)
    gboml_model.add_nodes_in_model(*nodes)
    gboml_model.add_hyperedges_in_model(*edges)
    gboml_model.build_model()
    solution, obj, status, solver_info, constr_info, _ = gboml_model.solve_gurobi()
    print("Solved")
    gathered_data = gboml_model.turn_solution_to_dictionary(solver_info, status, solution, obj, constr_info)
   
    
    if hydrogen_demand != 0:
        commodity_changed = 'hydrogen'
    elif water_demand != 0:
        commodity_changed = 'water'
    elif co2_demand != 0:
        commodity_changed = 'co2'
    else:
        commodity_changed = ''
    
    out_dir = 'commodity_cost_results'
    os.makedirs(out_dir, exist_ok=True)
    scenario_nbre = os.path.split(file_name)[-1]
    
    out_file = os.path.join(out_dir,scenario_nbre)
    with open(out_file + '_' + commodity_changed + '.json', "w") as fp:
        json.dump(gathered_data, fp, indent=4)
    
    print(out_file + '_' + commodity_changed + '.json saved')
    
    return 1, out_file + '_' + commodity_changed + '.json'


def save_value_in_file(output_file_name, commodity, cost):  # commodity is a string while cost is a float object
    with open (output_file_name, 'a') as output_file:
        output_file.write('\n')
        output_file.write(commodity)
        if commodity == 'wind_hub' or commodity =='solar_pv_hub' or commodity == 'wind_be' or commodity == 'solar_pv_be':
            output_file.write(' : %lf €/MWh' % cost)
        else: 
            output_file.write(' : %lf €/t' % cost)
        
    print(output_file_name + ' saved')
    
    return
    

def commodity_price(output_file, commodity, renewable_energy):
    
    out_file_name = os.path.join(os.path.split(output_file)[0], 'commodity_cost.txt')
    with open(output_file) as file: 
        data = json.load(file)
        
        
    """ Commodity cost calculation """
        
    if commodity == 'hydrogen':
        objective = data["solution"]["objective"]  # MEur
        total_hydrogen_production = sum(data["solution"]["elements"]["ELECTROLYSIS_PLANTS"]["variables"]["hydrogen_out"]["values"]) # kt
        commodity_cost = objective * 1000000 / (total_hydrogen_production * 1000) # Eur/t
        
    elif commodity == 'water':
        objective = data["solution"]["objective"]  # MEur
        total_water_production = sum(data["solution"]["elements"]["DESALINATION_PLANTS"]["variables"]["water_out"]["values"]) # kt
        commodity_cost = objective * 1000000 / (total_water_production * 1000) # Eur/t
    
    elif commodity == 'co2_s1':
        objective = data["solution"]["objective"]  # MEur
        total_carbon_dioxide1_production = sum(data["solution"]["elements"]["DIRECT_AIR_CAPTURE_PLANTS_BASED_ON_SOLID_ADSORPTION"]["variables"]["co2_out"]["values"]) # kt
        commodity_cost = objective * 1000000 / (total_carbon_dioxide1_production * 1000) # Eur/t
    
    elif commodity =='co2_s2':
        objective = data["solution"]["objective"]  # MEur
        total_carbon_dioxide2_production = sum(data["solution"]["elements"]["PIPE_CO2_ON_SHORE_VERY_BIG"]["variables"]["flow_out"]["values"]) # kt
        commodity_cost = objective * 1000000 / (total_carbon_dioxide2_production * 1000) # Eur/t
        
    elif commodity == 'co2_s3':
        objective = data["solution"]["objective"]  # MEur
        total_carbon_dioxide3_production = sum(data["solution"]["elements"]["PCCC_BE"]["variables"]["co2_source"]["values"])   # kt
        commodity_cost = objective * 1000000 / (total_carbon_dioxide3_production * 1000) # Eur/t
        
    else:
        return
    
    save_value_in_file(out_file_name, commodity, commodity_cost)
    
    
    """ electricity cost calculation """
    
    if renewable_energy != 0:
        
        wind_hub_objective = sum(data["solution"]["elements"]["WIND_PLANTS"]["objectives"]["unnamed"])  # MEur
        total_wind_hub_elec_out = sum(data["solution"]["elements"]["WIND_PLANTS"]["variables"]["elec_out"]["values"]) # Gwh       
        wind_hub_cost = wind_hub_objective * 1000000 / (total_wind_hub_elec_out * 1000) # Eur / MWh
        
        pv_hub_objective = sum(data["solution"]["elements"]["SOLAR_PV_PLANTS"]["objectives"]["unnamed"])  # MEur
        total_pv_hub_elec_out = sum(data["solution"]["elements"]["SOLAR_PV_PLANTS"]["variables"]["elec_out"]["values"]) # Gwh
        pv_hub_cost = pv_hub_objective * 1000000 / (total_pv_hub_elec_out * 1000) # Eur / MWh
        
        wind_be_objective = sum(data["solution"]["elements"]["WIND_PLANTS_BE"]["objectives"]["unnamed"])  # MEur
        total_wind_be_elec_out =  sum(data["solution"]["elements"]["WIND_PLANTS_BE"]["variables"]["elec_out"]["values"]) # GWh
        wind_be_cost = wind_be_objective * 1000000 / (total_wind_be_elec_out * 1000) # Eur / MWh
        
        pv_be_objective = sum(data["solution"]["elements"]["SOLAR_PV_PLANTS_BE"]["objectives"]["unnamed"])  # MEur
        total_pv_be_elec_out =  sum(data["solution"]["elements"]["SOLAR_PV_PLANTS_BE"]["variables"]["elec_out"]["values"]) # GWh
        pv_be_cost = pv_be_objective * 1000000 / (total_pv_be_elec_out * 1000) # Eur / MWh
        
        
        
        
        
        save_value_in_file(out_file_name,'wind_hub', wind_hub_cost)
        save_value_in_file(out_file_name,'solar_pv_hub', pv_hub_cost)
        save_value_in_file(out_file_name,'wind_be', wind_be_cost)
        save_value_in_file(out_file_name,'solar_pv_be', pv_be_cost)
        
        
        
        
    return
    
