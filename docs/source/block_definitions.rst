Block Definitions
-----------------

In order to implement an instance of the abstract GBOML problem, the model must be encoded in an input file written in the GBOML grammar.
This input file is structured into blocks, which are introduced by one of the following keywords, namely :math:`\texttt{#TIMEHORIZON}`, :math:`\texttt{#GLOBAL}`, :math:`\texttt{#NODE}`, and :math:`\texttt{#HYPEREDGE}`. The time horizon information is given in the :math:`\texttt{#TIMEHORIZON}` block, which must be the first one defined in the input file. Global parameters must be defined in the :math:`\texttt{#GLOBAL}` block, which must come in second position. Then, each node can be defined in a :math:`\texttt{#NODE}` block, while each hyperedge can be defined in a :math:`\texttt{#HYPEREDGE}` block. Note that the order in which :math:`\texttt{#NODE}` and :math:`\texttt{#HYPEREDGE}` blocks appear in the input file does not matter (i.e., hyperedge definitions may precede node definitions and vice-versa). Thus, an input file is typically structured as follows:

.. code-block:: c

   #TIMEHORIZON
   // time horizon definition

   #GLOBAL
   // global parameters

   #NODE <identifier>
   // first node definition

   #NODE <identifier>
   // second node definition

   #HYPEREDGE <identifier>
   // first hyperedge definition

   // possibly further node blocks

   #HYPEREDGE <identifier>
   // second hyperedge definition

   // possibly further hyperedge blocks

These different blocks are further discussed in this section:

.. toctree::
   :maxdepth: 4

   ./time_horizon.rst
   ./global_parameters.rst
   ./nodes.rst
   ./hyperedges.rst
