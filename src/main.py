# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).

"""GBOML compiler main file, compiles input file given in command line.

GBOML is an algebraic modelling language developed at the UNIVERSITY OF LIEGE.
This compiler takes GBOML input files and converts them into matrices to send
to solvers. Furthermore, once the problem solved, it outputs the results in an
understandable formalism similar to the input file.

  Typical usage example:

   $ python main.py gboml_file.txt --solver --output_type
  where:
    gboml_file is the file we want to compile
    --solver can either be linprog, cplex, clp/cbc, gurobi, xpress
    --output_type can either be csv or json

Several other options exists and can be retrieved by writing :
  python main.py -h
"""


from gboml import main


if __name__ == '__main__':
    main()
