Logical Conditions
==================

Besides their immediate use in model equations, expressions can be further used to construct logical conditions. More specifically, logical conditions are constructed from expressions, comparison operators, and logical operators.

Let :math:`\texttt{t}` denote an integer. Then, the following logical conditions are valid in GBOML:

.. math::

    \texttt{t > 0 and t <= 10}, \qquad \texttt{t < 2 or t > 4}, \qquad \texttt{not mod(t,5) == 0}.

Note that conditions can be used to selectively enforce constraints over a subset of indices, which is discussed when introducing the :math:`\texttt{#CONSTRAINTS}` block.
