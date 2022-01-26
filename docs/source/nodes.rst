Nodes
-----

In the hypergraph abstraction of optimization problems underpinning the GBOML language, nodes represent optimization subproblems. Hence, each node has its own set of parameters. It is also equipped with a set of variables, which are split into *internal* and *external* (or *coupling*) variables. In addition, a set of constraints can be defined for each node, along with a local objective function representing its contribution to a system-wide objective.

A unique identifier must be assigned to each :math:`\texttt{#NODE}` block, and such a block is further divided into code blocks where parameters, variables, constraints, and objectives can  be defined.
Each of these blocks is introduced by one of the following keywords, namely :math:`\texttt{#PARAMETERS}`, :math:`\texttt{#VARIABLES}`, :math:`\texttt{#CONSTRAINTS}`, and :math:`\texttt{#OBJECTIVES}`.
A typical :math:`\texttt{#NODE}` block is therefore structured as follows:

.. code-block:: c

   #NODE <node identifier>
   #PARAMETERS
   // parameter definitions
   #VARIABLES
   // variable definitions
   #CONSTRAINTS
   // constraint definitions
   #OBJECTIVES
   // objective definitions

These different code blocks are discussed in further detail below.

Parameters
==========

The parameters defined within a given :math:`\texttt{#NODE}` block respect the same rules as those defined in the :math:`\texttt{#GLOBAL}` block. However, node parameters are local to the present node and parameters defined in different nodes cannot be accessed in this scope.

For the sake of illustration, the following :math:`\texttt{#PARAMETERS}` block is valid in GBOML:

.. code-block:: c

  #PARAMETERS
  gravity       = 9.81;
  speed         = import "speed.txt";

Variables
=========

Variables are declared with one of the two keywords :math:`\texttt{internal}` and :math:`\texttt{external}`. While :math:`\texttt{internal}` variables are meant to model the internal state of a node, :math:`\texttt{external}` variables are meant to model the interaction between different nodes.
That is, the coupling between nodes is modeled by imposing constraints on their :math:`\texttt{external}` variables (which is further discussed when introducing :math:`\texttt{#HYPEREDGE}` blocks). In addition, variables can represent either a scalar or a vector. The syntax for declaring variables in GBOML is as follows:

.. code-block:: c

  internal : <identifier>;
  external : <identifier>;
  internal : <identifier> [ <expression> ];
  external : <identifier> [ <expression> ];

Variables defined only by an identifier are scalar variables, with the identifier giving its name to the variable (Rules 1 and 2). An expression can be added after the identifier to declare a vector variable and specify its length (Rules 3 and 4).

Furthermore, variables can be of different types, which can be specified by using one additional keyword when declaring a variable, namely :math:`\texttt{continuous}`, :math:`\texttt{integer}` or :math:`\texttt{binary}`. Note that if no keyword is specified, variables are assumed to be continuous by default.

Given these syntax rules, the following :math:`\texttt{#VARIABLES}` block is valid in GBOML:

.. code-block:: c

   #VARIABLES
   internal integer : x; // internal integer scalar variable
   internal binary  : y[T]; // internal binary variable vector of size T
   external : inflow[1000]; // external continuous variable vector of size 1000
   external : outflow[1000]; // external continuous variable vector of size 1000

Constraints
===========

The syntax rules for the definition of basic equality and inequality constraints are as follows:

.. code-block:: c

 <expression> == <expression>;
 <expression> <= <expression>;
 <expression> >= <expression>;

Therein, both the left-hand side and the right-hand side of the constraints are general expressions while the type of the constraint is indicated by the comparison operator used.
Furthermore, in line with the fact that parameter and variable definitions are local to a given node, constraints defined in a :math:`\texttt{#NODE}` block must not reference quantities that are defined in other nodes.

An identifier can be also be assigned to constraints when defining them. The following syntax can be used to do so:

.. math::

    \texttt{<constraint identifier>: <constraint>;}

Assigning an identifier to constraints makes it possible to uniquely identify them and query additional information from the solver (e.g., retrieve dual variables and slacks).

Given these syntax rules, the following is an example of valid constraint definitions within an appropriate node and time horizon context:

.. code-block:: c

 #TIMEHORIZON
 T = 2;

 #NODE mynode
 #PARAMETERS
 a = {2,4};
 #VARIABLES
 internal : x[T];
 external : outflow[T];
 #CONSTRAINTS
 initial_constraint : x[0] >= 0;
 x[1] >= 0;
 x[2] <= a[1];
 outflow[1] == sum(x[i] for i in [0:T-1]);
 #OBJECTIVES
 // objective definitions

Note that the variables and the parameter are only accessed at indices that are consistent with their definitions.

GBOML provides two options to specify expansion ranges and define vectorized constraints, namely user-defined and automatic expansions.

First, user-defined expansions can be constructed as follows:

.. code-block:: c

 <constraint> <expansion range>;

where :math:`\texttt{<constraint>}` is an equality or inequality constraint and :math:`\texttt{<expansion range>}` can be expressed using the :math:`\texttt{for}` and :math:`\texttt{where}` keywords, according to the following syntax rules:

.. math::

 {\small
 \begin{align*}
 \texttt{<expansion range>} &\texttt{:= for <identifier> in [<start>:<end>];}\\
                             &\texttt{:= for <identifier> in [<start>:<step>:<end>];}\\
                             &\texttt{:= for <identifier> in [<start>:<end>] where <condition>;}\\
                             &\texttt{:= for <identifier> in [<start>:<step>:<end>] where <condition>;}\\
 \end{align*}}

The first rule defines a constraint that is applied for all integral values of :math:`\texttt{<identifier>}` that lie in the range between :math:`\texttt{<start>}` and :math:`\texttt{<end>}` (both included). Note that :math:`\texttt{<start>}` must be smaller than :math:`\texttt{<end>}` for the range to be non-empty. If an empty range is given, a warning will be raised. The :math:`\texttt{<identifier>}` may be any identifier that has not been used to define a parameter or a variable in the present node block. The :math:`\texttt{t}` identifier is reserved for automatic expansion (discussed below) and may not be used for user-defined expansions. The second rule makes use of the optional definition of a :math:`\texttt{<step>}` that is used to increment through the range between :math:`\texttt{<start>}` and :math:`\texttt{<end>}`. The third and fourth rules are only extensions of the first two, where a certain :math:`\texttt{condition}` needs to be satisfied for the constraint to be expanded. Recall that such conditions are defined in terms of expressions, comparison operators, and logical operators. For a condition to be valid, it must be possible to evaluate it for a given value of :math:`\texttt{<identifier>}`. In particular, conditions may depend on :math:`\texttt{<identifier>}` and parameters but must not depend on variables. In addition, the indices over which expansions take place must be valid for vectors of parameters and variables involved in vectorized constraints. More precisely, an index is valid if it is non-negative and does not exceed the size of said vector. If an index that is not valid is used in the expansion, an error is returned.

Second, automatic expansions can be declared by using the :math:`\texttt{t}` identifier in a constraint. The constraint is then expanded over all valid indices :math:`\texttt{t} \in \{0,...,T-1\}`.

For example, the following vectorized constraint

.. code-block:: c

 x[t] >= x[t-5];

will only be expanded over :math:`\texttt{t} \in \{5,...,\texttt{T}-1\}` since the right-hand side expression is ill-defined for :math:`\texttt{t} < 5`. A warning is also raised to indicate the values of :math:`\texttt{t}` over which the constraint cannot be expanded. Furthermore, a condition can be added in automatic expansions. The corresponding syntax rule can be written as:

.. code-block:: c

 <constraint> <condition>;

where :math:`\texttt{condition}` may depend on :math:`\texttt{t}` and parameters.

The following is an example illustrating both expansion methods and making use of the keywords :math:`\texttt{for}` and :math:`\texttt{where}` in order to compactly write selectively-imposed constraints:

.. code-block:: c

 #TIMEHORIZON
 T = 20;

 #NODE mynode
 #PARAMETERS
 a = import "data.csv"; // parameter vector with 20 entries
 #VARIABLES
 internal : x[T];
 external : outflow[T];
 #CONSTRAINTS
 nonnegativity : x[t] >= 0;
 x[i] <= a[i] for i in [1:(T-2)/2];
 0 <= a[i]*x[i] for i in [2:2:10] where i != 4;
 x[t] == 0 where t == 0 or t == T-1;
 outflow[0] == x[0];
 outflow[t] == outflow[t-1] + x[t];
 #OBJECTIVES
 // objective definitions

While the syntax discussed above is sufficiently expressive to define nonlinear equality and inequality constraints, the GBOML parser expects constraints to be affine with respect to all variables involved. Hence, encoding nonlinear constraints leads to an error being raised.

Objectives
==========

Objective definitions are given by an expression and a keyword indicating whether the objective should be minimized or maximized.
The syntax rules for the definition of objectives are as follows:

.. code-block:: c

 min : <expression>;
 max : <expression>;
 min : <expression> <expansion range>;
 max : <expression> <expansion range>;

At least one node in a given model must possess at least one objective but all nodes may have multiple objectives. In case multiple objectives are given in the same :math:`\texttt{#NODE}` block, all objectives are aggregated into a single one by summing them (respecting the sign associated with the keywords :math:`\texttt{min}` and :math:`\texttt{max}`).
Since the abstract GBOML problem is a minimization problem, the signs of objectives that should be maximized are inverted before summation.

Objectives can also be expanded in two ways, namely via user-defined and automatic expansions. First, user-defined expansions make use of an :math:`\texttt{<identifier>}` that will be expanded over each value in the :math:`\texttt{<expansion range>}`. Second, automatic expansions can be constructed by using the :math:`\texttt{t}` identifier directly in the objective. Since all local objectives defined in the same :math:`\texttt{#NODE}` block are eventually aggregated, the following objectives are in fact equivalent:

.. math::

 \texttt{min : x[t]}, \quad \texttt{min : sum(x[i] for i in [0:T-1])}

Similarly to constraints, identifiers can be assigned to objectives when defining them using the following syntax:

.. code-block:: c

   min <identifier>: <expression>;
   max <identifier>: <expression>;
   min <identifier>: <expression> <expansion range>;
   max <identifier>: <expression> <expansion range>;

The previous example can be completed by defining an objective function, which yields a complete and valid :math:`\texttt{#NODE}` block:

.. code-block:: c

 #TIMEHORIZON
 T = 20;

 #NODE mynode
 #PARAMETERS
 a = import "data.csv"; // parameter vector with 20 entries
 #VARIABLES
 internal : x[T];
 external : outflow[T];
 #CONSTRAINTS
 x[t] >= 0;
 x[t] <= a[t] for t in [1:T-2];
 x[t] == 0 where t == 0 or t == T-1;
 outflow[0] == x[0];
 outflow[t] == outflow[t-1] + x[t];
 #OBJECTIVES
 max final_outflow: outflow[T-1];

As for constraint definitions, the syntax for objective definitions is sufficiently expressive to define nonlinear objectives.
However, the GBOML parser expects all objectives to be affine with respect to all variables.
