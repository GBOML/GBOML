# GBOML Compiler
## Project
This repository is the official repository of the graph-based optimization modeling language (GBOML). GBOML enables the easy implementation of a broad class of structured mixed-integer linear programs typically found in applications ranging from energy system planning to supply chain management. More precisely, the language is particularly well-suited for representing problems involving the optimization of discrete-time dynamical systems over a finite time horizon and possessing a block decomposable structure that can be encoded by a sparse connected hypergraph. The language combines elements of both algebraic and object-oriented modeling languages in order to facilitate problem encoding and post-processing. A tutorial can be found at http://hdl.handle.net/2268/256705.

## Installing
You need to install the requirements :
```
pip install -r requirements.txt
```
Now you are able to use Linprog as a solver (for linear programs)

## Installing other solvers:
### Gurobi:
To be able to use Gurobi please install :

>https://www.gurobi.com/

Then,

```
python -m pip install -i https://pypi.gurobi.com gurobipy
```
### CPLEX:
To be able to use CPLEX please install :

>https://www.ibm.com/support/pages/downloading-ibm-ilog-cplex-optimization-studio-2010

Then,

```
pip install cplex
```

### CBC/CLP
To be able to use Cbc please install :
>https://projects.coin-or.org/Cbc

Then,

```
pip install cylp
```
### Communicating with solver APIs
In order to pass arguments to solvers, they can be written in an auxiliary input file with the following naming convention :
```
solver_name.opt
```

## Usage
The command line goes as follows,
```
python main.py <file>
```
List of optional arguments

-**Print tokens:** To print the tokens outputted by the lexer you can add  

```
--lex
```

-**Print the syntax tree:** To print the syntax tree by the parser you can add

```
--parser
```

-**Print the matrices:** To print the matrix A, the vector b and C

```
--matrix
```

-**Linprog:** Use Linprog solver

```
--linprog
```

-**Gurobi** Use Gurobi solver

```
--gurobi
```

-**CPLEX** Use CPLEX solver

```
--cplex
```

-**Cbc** Use Cbc solver

```
--cbc
```

-**CSV :** Output format CSV

```
--csv
```

-**JSON** Output format json

```
--json
```

-**OUTPUT** Set the output name and directory

```
--output path/filename
```

### Changes from V0.0.1 to V0.0.2
V0.0.2 comes with a broad range of additional functionalities. First, the more fundamental changes are:

- The keywords input/output have been replaced by the keyword external.

- Variables have sizes. (note that vector variables must be indexed wherever they appear and may no longer be referred to by their identifier alone)

- the keyword #LINKS does not exist anymore and has been replaced by #HYPEREDGE definitions

The new functionalities are : 

- The sum operator

- Hyperlink definitions with its set of parameters and constraints

- Mixed-Integer Linear Programming

- Global parameters

For more informations, please refer to the tutorial http://hdl.handle.net/2268/256705.

###Citation
To cite this repository : 
```
@misc{GBOML,
  title={{GBOML} {R}epository: {G}raph-{B}ased {O}ptimization {M}odeling {L}anguage},
  author={Miftari, Bardhyl and Berger, Mathias and Bolland, Adrien and Djelassi, Hatim and Ernst, Damien},
  institution={ULiege Smart Grids Lab},
  year={2021},
  note={URL : https://gitlab.uliege.be/smart\_grids/public/gboml}
}
```
To cite the tutorial : 
```
@misc{GBOMLtutorial,
author={Berger, Mathias and Bolland, Adrien and Miftari, Bardhyl and Djelassi, Hatim and Ernst, Damien},
title={{G}raph-{B}ased {O}ptimization {M}odelling {L}anguage: A {T}utorial},
institution={University of Li{\e`}ge},
year={2021},
note={URL : http://hdl.handle.net/2268/256705}
}
```