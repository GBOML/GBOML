*GBOML: Graph-Based Optimization Modeling Language*

---
## Contents of files
The source code of the GBOML Solver is divided in XX parts : 
- cbc_solver.py contains a new experimental direct interface to CBC via pycbc
- clp_solver.py contains a CBC/CLP interface from GBOML via CyLP
- cplex.opt contains an example of parameters file that can be passed to cplex 
  (in this case those parameters will be used by default)
- cplex_solver.py contains the GBOML interface to CPLEX
- dsp_solver.py contains the GBOML interface to DSP via its experimental interface dsppy.py
- dsppy.py contains the ctypes experimental interface to DSP via its shared object
- gurobi.opt contains an example of parameters file that can be passed to gurobi 
  (in this case those parameters will be used by default)
- gurobi_solver.py contains the GBOML interface to Gurobi
- highs.opt contains an example of parameters file that can be passed to HiGHS
  (in this case those parameters will be used by default)
- highs_solver.py contains the GBOML HiGHS interface via the experimental package pyhighs.py
- pycbc.py contains the ctypes experimental interface to CBC via its shared object
- pyhighs.py contains the ctypes experimental interface to HiGHS via its shared object
- scipy_solver.py contains a basic interface to the scipy solver (it does not support intergers variables)
- xpress.opt contains an example of parameters file that can be passed to HiGHS
  (in this case those parameters will be used by default)
- xpress_solver.py contains the GBOML interface to Xpress via the xpress package