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

### Cbc
To be able to use Cbc please install :
>https://projects.coin-or.org/Cbc

Then,

```
pip install cbcpy
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
