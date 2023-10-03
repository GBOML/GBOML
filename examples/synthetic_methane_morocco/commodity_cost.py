import argparse
import gboml_functions as gf
import os


""" Production of a txt file with cost commodity per commodity unit """

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-n1', '--name1', help='Name gboml file scenario 1',
                        type=str, default=os.path.join('gboml_models','scenario_1.txt'))
    parser.add_argument('-n2', '--name2', help='Name gboml file scenario 2',
                        type=str, default=os.path.join('gboml_models','scenario_2.txt'))
    parser.add_argument('-n3', '--name3', help='Name gboml file scenario 3',
                        type=str, default=os.path.join('gboml_models','scenario_3.txt'))
    parser.add_argument('-y', '--years', help='Number of years',
                        type=int, default=1)
    parser.add_argument('-md', '--methane_demand', help='Methane demand in kt / h',
                        type=float, default=0)
    parser.add_argument('-cd', '--co2_demand', help='CO2 demand in kt / h',
                        type=float, default=0.5)
    parser.add_argument('-hd', '--hydrogen_demand', help='Hydrogen demand in kt / h',
                        type=float, default=1)
    parser.add_argument('-wd', '--water_demand', help='Water demand in kt / h',
                        type=float, default=1)
    
    args = parser.parse_args()
    
    name1 = args.name1
    name2 = args.name2
    name3 = args.name3
    years = args.years
    methane_demand = args.methane_demand
    co2_demand = args.co2_demand
    hydrogen_demand = args.hydrogen_demand
    water_demand = args.water_demand
    timehorizon = 365*24*years
    
    """ Commodity cost per commodity unit calculation """
    """ Values saved in a .txt file """
    
    gf.main(name1,timehorizon,methane_demand,hydrogen_demand,0,0,0,0) # only hydrogen demand
    gf.main(name1,timehorizon,methane_demand,0,water_demand,0,0,0)    # only water demand
    gf.main(name1,timehorizon,methane_demand,0,0,co2_demand,1,0)      # only co2 demand in scenario 1
    gf.main(name2,timehorizon,methane_demand,0,0,co2_demand,2,0)      # only co2 demand in scenario 2
    gf.main(name3,timehorizon,methane_demand,0,0,co2_demand,3,1)      # only co2 demand in scenario 3 + renewable energy cost

        
    
    
