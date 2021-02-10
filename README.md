# GBOML Compiler
## Installing 
You need to install the requirements : 
```
pip install -r requirements.txt
```
Now you are able to use Linprog as a solver

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

### CLP
To be able to use CLP please install : 
>https://projects.coin-or.org/Clp

Then, 

```
pip install cylp
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

-**CLP** Use CLP solver

```
--clp
```

-**CSV :** Output format CSV 

```
--csv
```

-**JSON** Output format json

```
--json
```