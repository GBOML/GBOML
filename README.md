# Compiler name
## Installing 
To be able to use Gurobi please install : 

>https://www.gurobi.com/

>https://julialang.org/downloads/

You need to install the requirements : 
```
pip install -r requirements
```
The start a python REPL:
```
python 
```
Execute the two commands : 
```
import julia
julia.install()
```
Normally you are good to go ! 

## Usage 
The command line goes as follows,
```
python main.py <file> 
```
List of optional arguments

-**Print tokens:**

    To print the tokens outputted by the lexer you can add  
    ```
    --lex
    ```

-**Print the syntax tree:**

    To print the syntax tree by the parser you can add
    ```
    --parser
    ```

-**Print the matrices:**

    To print the matrix A, the vector b and C
    ```
    --matrix
    ```

-**Linprog:** 

    Use Linprog solver instead of Gurobi
    ```
    --linprog
    ```

-**CSV :** 

    Output format CSV (default)
    ```
    --csv
    ```

-**JSON**

    Output format json
    ```
    --json
    ```