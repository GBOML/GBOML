import argparse
import gboml_functions as gf
import os

""" Enable to run gboml files one after the other """

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-if', '--input_files', nargs = '*', help='names gboml files to be run',
                        type=str, default=[
                            os.path.join('gboml_models','scenario_1.txt'),
                            os.path.join('gboml_models','scenario_2.txt'),
                            os.path.join('gboml_models','scenario_3.txt'),
                            os.path.join('gboml_models','scenario_3_pipe.txt')])
    parser.add_argument('-y', '--years', help='Number of years',
                        type=int, default=1)
    
    
    args = parser.parse_args()
    
    files = args.input_files
    years = args.years
    timehorizon = 365*24*years
    
    for file in files:
        gf.gboml_graph_run(file, timehorizon)
        
    
    
    
