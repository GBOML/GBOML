Time Horizon
============

The time horizon :math:`\texttt{T}` defines the length of the optimization horizon (i.e., the number of time periods considered). This definition is contained in the :math:`\texttt{#TIMEHORIZON}` block, which is the first one that should appear in a GBOML file. This block has the following structure:

.. code-block:: c

   #TIMEHORIZON
   T = <expression>;

Therein, :math:`\texttt{<expression>}` is an algebraic expression that should evaluate to a positive integer. If :math:`\texttt{<expression>}` evaluates to a positive but non-integral value, it will be rounded to the closest integer automatically and a warning will be raised. Expressions that cannot be evaluated and expressions that evaluate to a negative value are not permitted. In addition, since the :math:`\texttt{#TIMEHORIZON}` block is the first block of any input file and no parameters can been defined before it, :math:`\texttt{<expression>}` may not depend on any parameters. An example of a valid :math:`\texttt{#TIMEHORIZON}` block is given below:

.. code-block:: c

   #TIMEHORIZON
   T = 24*5.5+6;

The definition of a time horizon has two effects on the remainder of the model. First, the time horizon can be addressed as a parameter anywhere in the model by referring to its identifier :math:`\texttt{T}`. Accordingly, the identifier :math:`\texttt{T}` is reserved and cannot be re-used for the definition of nodes, variables, or parameters in the remainder of the model. Second, constraints and objectives can be automatically expanded over the time full horizon by using the identifier :math:`\texttt{t}` as an index with vector variables. In other words, the constraints or objectives that use :math:`\texttt{t}` as an index are automatically expanded for each :math:`\texttt{t} \in \{0, 1, ..., T − 1\}.` Accordingly, :math:`\texttt{t}` is a reserved identifier that cannot be used for any other purpose.
