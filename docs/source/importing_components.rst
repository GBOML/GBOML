Importing Nodes and Hyperedges
------------------------------

Importing Nodes
~~~~~~~~~~~~~~~

A node can be defined by importing an existing node from a GBOML input file. The imported node can be used as such or some of its attributes may be re-defined (e.g., parameter values may be changed) based on the following syntax rules:

.. code-block:: c

 #NODE <new node identifier> = import <imported node identifier> from <filename>
 #NODE <new node identifier> = import <imported node identifier> from <filename> with <re-definitions>

If the imported node sits at the top of the node hierarchy in the GBOML input file, its identifier should be used as such after the *import* keyword. However, if the imported node happens to be deeper in the hierarchy, a sequence of dot-separated identifiers corresponding to its ancestors should be prefixed to its own identifier.
For example, for a GBOML file with a 2-level hierarchy, a child node could be imported by using the following identifier:

.. math::

    \texttt{<parent node identifier>.<child node identifier>}

When importing a node, two types of re-definitions are possible:

 * Re-defining parameter values (i.e., changing the value of an existing parameter).

 * Re-defining variable type (i.e., from external to internal or vice-versa).

To re-define the values of parameters originally defined in the imported node, their identifiers must be followed by equality signs and new values:

.. code-block:: c

	#NODE <new node identifier> = import <imported node identifier> from <filename> with <parameter identifier> = <new parameter value>;

Note that the re-definition of a parameter may not change its type (i.e., vectors must remain vectors and likewise for scalars).
In addition, several parameters can be re-defined in such fashion, provided that each assignment is followed by a semi-colon.

Variable type can be re-defined with the following rules:

.. code-block:: c

 <variable identifier> external;
 <variable identifier> internal;

To illustrate these features, let *file1.txt* be a GBOML input file from which a node should be imported:

.. code-block:: c

  //file1.txt
  #NODE Consumers
  #PARAMETERS
  total_number = 10;

    #NODE consumer_1
    #PARAMETERS
    price_per_unit = 5;
    avg_number_of_units = 100;
    #VARIABLES
    internal : delivery[T];

  #VARIABLES
  internal : consumer_1_delivery[T] <- consumer_1.delivery[T];

Let *consumer_1* be the identifier of the node that should be imported. This node can be imported in another file *file2.txt* as follows:

.. code-block:: c

  //file2.txt
  #NODE average_consumer = import Consumers.consumer_1 from "file1.txt" with
    price_per_unit = 6;
    delivery external;

This block defines the *average_consumer* node by importing the *consumer_1* node from *file1.txt*. It re-defines its *price_per_unit* parameter in the process and also changes the type of the *delivery* variable from *internal* to *external*.

Importing Hyperedges
~~~~~~~~~~~~~~~~~~~~

Hyperedges may also be imported from a GBOML file using similar rules:

.. code-block:: c

 #HYPEREDGE <new hyperedge identifier> = import <identifiers> from <filename>
 #HYPEREDGE <new hyperedge identifier> = import <identifiers> from <filename> with <re-definitions>

The first rule works just like the one described above for nodes. The second rule, however, differs in its possible re-definitions. More precisely, parameter values may be re-defined but variable types may not, since hyperedges do not have their own variables. However, the identifiers of nodes appearing in a hyperedge may be modified as follows:

.. code-block:: c

	<old node identifier> <- <new node identifier>;

This rule changes all occurrences of the old node identifier by the new identifier in the hyperedge.

To illustrate these features, let *file3.txt* be a GBOML input file from which a hyperedge should be imported:

.. code-block:: c

  //file3.txt
  #NODE A
  #VARIABLES
  external : x[t];
  #CONSTRAINTS
  x[t]>= 2;
  #OBJECTIVES
  min: x[t];

  #NODE B
  #VARIABLES
  external : x[t];
  #CONSTRAINTS
  x[t]>= 3;
  #OBJECTIVES
  min: x[t];

  #HYPEREDGE H
  #CONSTRAINTS
  A.x[t] + B.x[t] >=6;

Let :math:`\texttt{H}` be the identifier of the hyperedge that should be imported. Let us consider a second file named *file4.txt* in which :math:`\texttt{H}` should be re-named as :math:`\texttt{H_1}` and link two nodes named :math:`\texttt{C}` and :math:`\texttt{D}`. This file is given as follows:

.. code-block:: c

  //file4.txt
  #NODE C
  #VARIABLES
  external : x[t];
  #CONSTRAINTS
  x[t]>= 5;
  #OBJECTIVES
  min: x[t];

  #NODE D
  #VARIABLES
  external : x[t];
  #CONSTRAINTS
  x[t]>= 6;
  #OBJECTIVES
  min: x[t];

  #HYPEREDGE H_1 = import H from "file1.txt" with
    A <- C;
    B <- D;

The last code block imports the hyperedge :math:`\texttt{H}` and re-names all occurrences of node :math:`\texttt{A}` by node :math:`\texttt{C}` and node :math:`\texttt{B}` by node :math:`\texttt{D}`. It is therefore equivalent to defining:

.. code-block:: c

  #HYPEREDGE H_1
  #CONSTRAINTS
  C.x[t] + D.x[t] >= 6;
