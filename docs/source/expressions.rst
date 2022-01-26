Expressions
===========

Algebraic expressions are used to construct the different components of a model, such as its constraints and objective. Expressions typically involve numbers and identifiers referring to parameters and variables, along with some of the operators introduced previously.
While numbers are always scalar, variables and parameters may be either scalars or vectors (of any length). Their entries are accessed via an index written in brackets :math:`\texttt{[}` and :math:`\texttt{]}`. For the sake of illustration, let :math:`\texttt{v}` be an identifier referring to a vector quantity of length :math:`\texttt{L}`. Then, the entries of :math:`\texttt{v}` are accessed via

.. math::

    \texttt{v[0]}, \qquad \texttt{v[1]}, \qquad \texttt{v[2]}, \qquad \dots, \qquad \texttt{v[L-1]}.


Note that the first index is :math:`\texttt{0}` and not :math:`\texttt{1}`.

Let :math:`\texttt{x}` and :math:`\texttt{v}` be the identifiers of a scalar quantity and a vector quantity, respectively. Then, the following expressions are valid in GBOML:

.. math::

    \texttt{x**2 - 6.5*x - 9}, \qquad \texttt{sum((i - 2.5)/3 for i in [0:10])}, \qquad \texttt{v[0] + v[mod(3,2)]}

Note that the above expressions contain whitespace characters, which are not required. Indeed, all kinds of whitespace characters (space, tabulation, line feed, form feed, and carriage return) are ignored by the GBOML compiler.
