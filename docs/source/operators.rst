Operators
=========

GBOML provides the following operators for elementary floating-point arithmetic, which are listed in order of decreasing precedence:

#. Exponentiation: :math:`\texttt{**}`
#. Multiplication: :math:`\texttt{*}` and Division: :math:`\texttt{/}`
#. Addition: :math:`\texttt{+}` and Subtraction: :math:`\texttt{-}`

Operator precedence can be overridden by using parentheses :math:`\texttt{(}`` and :math:`\texttt{)}`.
Besides these elementary arithmetic operators, GBOML provides the modulo operator and the sum operator as native functions:

* Modulo: :math:`\texttt{mod(<dividend>, <divisor>)}`
* Sum: :math:`\texttt{sum(<expression> for <id> in [<start>, <end>])}`

In addition, a set of comparison operators are available in the language:

* Equal to: :math:`\texttt{==}`
* Not equal to: :math:`\texttt{!=}`
* Less than or equal to: :math:`\texttt{<=}`
* Greater than or equal to: :math:`\texttt{>=}`
* Less than: :math:`\texttt{<}`
* Greater than: :math:`\texttt{>}`

Finally, a set of logical operators are available, listed below in order of decreasing precedence:

#. Negation: :math:`\texttt{not}`
#. Conjunction: :math:`\texttt{and}`
#. Disjunction: :math:`\texttt{or}`

Note that the precedence of logical operators can also be overriden by using parentheses.
