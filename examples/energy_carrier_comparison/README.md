# Remote Hub Multi Carrier

In order to reproduce the results obtained run :

```
python main.py -v "Name of the vector" 

Vectors : Ammonia, Hydrogen, Methane or Methanol

optional arguments : 
-> -th for Time Horizon, default 8760
-> -nn for Name Node, to modify a node in the GBOML file 
-> -np for Name Param, to select the modified node parameter 
-> -vp for Value Param, to modify the value of the parameter 

```

In order to display the results :

```
python analysis.py -v "Name of the vector"
 
same as the previous line of code -> just change main.py by analysis.py

```
