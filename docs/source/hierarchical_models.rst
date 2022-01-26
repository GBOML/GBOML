Hierarchical Models
===================

In the hierarchical hypergraph abstraction underpinning the GBOML language, each node can itself be viewed as a hierarchical hypergraph. Nodes may therefore be constructed in a bottom-up fashion, from *sub-nodes* linked by *sub-hyperedges*.

Sub-nodes and sub-hyperedges are defined between the :math:`\texttt{#PARAMETERS}` and :math:`\texttt{#VARIABLES}` blocks of a parent node. Thus, a typical hierarchical block :math:`\texttt{#NODE}` is structured as follows:

.. code-block:: c

   #NODE <parent node identifier>
   #PARAMETERS
   // parent parameter definitions

      #NODE <sub-node identifier 1>
      #PARAMETERS
      // sub-node 1 parameter definitions
      #VARIABLES
      // sub-node 1 variable definitions
      #CONSTRAINTS
      // sub-node 1 constraint definitions
      #OBJECTIVES
      // sub-node 1 objective definitions

      #NODE <sub-node identifier 2>
      #PARAMETERS
      // sub-node 2 parameter definitions
      #VARIABLES
      // sub-node 2 variable definitions
      #CONSTRAINTS
      // sub-node 2 constraint definitions
      #OBJECTIVES
      // sub-node 2 objective definitions

      #HYPEREDGE <sub-hyperedge identifier>
      #PARAMETERS
      // sub-hyperedge parameter definitions
      #CONSTRAINTS
      // sub-hyperedge constraint definitions

   #VARIABLES
   // parent variable definitions
   #CONSTRAINTS
   // parent constraint definitions
   #OBJECTIVES
   // parent objective definitions

Information can be exchanged between different levels in the hierarchy, notably through parameters and variables. However, the direction in which information can be shared between levels depends on its nature, as discussed below.

Parameters can be only passed from the top down. Hence, parameters defined in a parent node can be accessed in any child node or sub-hyperedge by prefixing the identifier of the parent node in any expression involving this parameter. In other words, parent node parameters can be accessed in child nodes as follows:

 .. math::

    \texttt{<parent node identifier>.<parameter identifier>}

Given these syntax rules, the following is a valid example of hierarchical parameter use (with three levels):

 .. code-block:: c

   #NODE A
   #PARAMETERS
   parameter_A = 1;

      #NODE B
      #PARAMETERS
      parameter_B = 2;

         #NODE C
         #PARAMETERS
         parameter_C = 3;
         sum_parameters = A.parameter_A + B.parameter_B + parameter_C; // = 6

Note that indenting node blocks corresponding to different levels in the hierarchy is not mandatory but makes for easier reading.

In contrast to parameters, variables can only be passed from the bottom up. Thus, a parent node can define some of its variables using those of a child node as follows:

 .. math::

   {\small
   \begin{align*}
   &\texttt{<parent node identifier> <- <child node identifier>.<variable identifier>};\\
   &\texttt{<parent node identifier> <- <child node identifier>.<variable identifier>[<expression>]};
   \end{align*}}

Note that parent variables defined in such fashion must have the same type as the underlying child variables and vector variables must also have the same length. In addition, parent variables can only be defined from child variables one level down in the hierarchy.

Given these syntax rules, the following is a valid example of hierarchical variable use:

 .. code-block:: c

   #NODE A

      #NODE B
      #VARIABLES
      internal : x[10];

      #NODE C
      #VARIABLES
      internal : x[10];

   #VARIABLES
   internal : y[10] <- B.x[10];
   external : z[10] <- C.x[10];

These two examples can be combined to produce a valid hierarchical model example:

 .. code-block:: c

   #TIMEHORIZON
   T = 10;

   #NODE A
   #PARAMETERS
   parameter_A = 1;

      #NODE B
      #PARAMETERS
      parameter_B = 1+A.parameter_A;
      #VARIABLES
      internal : x[10];
      #CONSTRAINTS
      x[t] >= parameter_B;

      #NODE C
      #PARAMETERS
      parameter_C = 2+A.parameter_A;
      #VARIABLES
      internal : x[10];
      #CONSTRAINTS
      x[t] >= parameter_C;

   #VARIABLES
   internal : y[10] <- B.x[10];
   external : z[10] <- C.x[10];
   #CONSTRAINTS
   y[t]+z[t] >= 6;
   #OBJECTIVES
   min: y[t]+z[t];
