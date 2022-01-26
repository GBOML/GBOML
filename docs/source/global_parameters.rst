Global Parameters
=================

The non-mandatory :math:`\texttt{#GLOBAL}` block contains the definitions of parameters that can be accessed anywhere in the model. This block is structured as follows:

.. code-block:: c

   #GLOBAL
   // global parameter definitions


A parameter definition maps an identifier to a fixed value, which may be either a scalar or a vector. The identifier must be unique within a given :math:`\texttt{#GLOBAL}` block and a value can be assigned to a parameter through one of the following three syntax rules:

.. code-block:: c

   < identifier > = < expression >;
   < identifier > = { < term > , < term > ,...};
   < identifier > = import " < filename >";

First, a scalar parameter is defined according to the first rule. Therein, :math:`\texttt{<expression>}` may be a scalar expression that evaluates to any floating-point number. In particular, it may contain global parameters that have been defined previously. If the parameter definition is valid with respect to these rules, a parameter named :math:`\texttt{<identifier>}` will be created and assigned the value of :math:`\texttt{<expression>}`.
Second, a vector parameter can be defined directly by providing a comma-separated list of values according to the second rule. Therein, each :math:`\texttt{<term>}` may be a floating-point number, a previously-defined scalar parameter, or an entry of a previously-defined vector parameter. The resulting vector parameter can be indexed in order to retrieve its constituent entries.
Third, a vector parameter can be defined by providing an input file according to the third rule. Therein, :math:`\texttt{<filename>}` refers to an input file in one of several delimiter-separated formats. The supported delimiter characters are comma, semicolon, space, and line feed. In contrast to the direct way of defining a vector parameter, the input file may only contain floating-point values and may not refer to other parameters.

Given these syntax rules, the following is an example of a valid :math:`\texttt{#GLOBAL}` block:

.. code-block:: c

   #GLOBAL
   pi = 3.1416;
   two_pi = 2* pi ;
   data = import " data . csv ";
   len_data = 23;
   angles = {0 , data [2] , two_pi };
   sum_data = sum ( data [ i ] for i in [0: len_data -1]) ;

Notably, the example makes use of the fact that previously-defined parameters can be employed to define new parameters. Furthermore, the parameters defined in this block can be accessed in any other block by referring to their identifier with the prefix :math:`\texttt{global}`. In other words, all global parameters are referred to as:

 .. math::

    \texttt{global.<parameter identifier>}

in the blocks that follow their definition.
