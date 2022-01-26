Python API Example
------------------

The following example illustrates various functions defined in the Python API and its *GbomlGraph* class.

First, the *GbomlGraph* class can be imported from the *gboml* package as follows:

.. code-block:: python

   from gboml import GbomlGraph

Second, an instance of the *GbomlGraph* class with a time horizon of 3 can be created:

.. code-block:: python

   timehorizon = 3
   gboml_model = GbomlGraph(timehorizon)

Third, all the nodes defined in the microgrid example can be imported:

.. code-block:: python

   nodes, edges = gboml_model.import_all_nodes_and_edges("examples/microgrid/microgrid.txt")

Then, the nodes and hyperedges may be re-named by adding "new\_" to the original names of all nodes and hyperedges,

.. code-block:: python

   old_names = []
   for node in nodes:
      old_names.append(node.get_name())
      gboml_model.rename(node, "new_"+node.get_name())

   for hyperedge in edges:
      gboml_model.rename(hyperedge, "new_"+hyperedge.get_name())
      for i, node in enumerate(nodes):
         gboml_model.change_node_name_in_hyperedge(hyperedge, old_names[i], node.get_name())

Let us assume that a node named :math:`\texttt{N}` exists in a GBOML file called *test6.txt*. In addition, let us assume that a variable :math:`\texttt{x[T]}`, a parameter :math:`\texttt{b=4}`, a constraint :math:`\texttt{x[t]>= b}` and an objective :math:`\texttt{min : x[t]}` are defined in this node.
Then, this node can be imported into a new node and the full microgrid problem can be encapsulated inside of it in order to create a hierarchy:

.. code-block:: python

   parent = gboml_model.import_node("test/test6.txt", "N")
   for node in nodes:
      gboml_model.add_sub_node(node, parent)

   for edge in edges:
      gboml_model.add_sub_hyperedge(edge, parent)

Note that at this stage, the *parent* node has not yet been added to the model and is currently a stand-alone imported Node object with sub-nodes and sub-hyperedges.

The value of the *parent* node parameter :math:`\texttt{b}` can be updated as follows:

.. code-block:: python

   gboml_model.redefine_parameters_from_keywords(parent, b=6)

Finally, the *parent* node can be added to the model. The latter can then be generated and solved with CPLEX:

.. code-block:: python

   gboml_model.add_nodes_in_model(parent)
   gboml_model.build_model()
   solution = gboml_model.solve_cplex()

To recap, the full code reads:

.. code-block:: python

   from gboml import GbomlGraph

   timehorizon = 3
   gboml_model = GbomlGraph(timehorizon)
   nodes, edges = gboml_model.import_all_nodes_and_edges("examples/microgrid/microgrid.txt")
   old_names = []
   for node in nodes:
      old_names.append(node.get_name())
      gboml_model.rename(node, "new_"+node.get_name())

   for hyperedge in edges:
      gboml_model.rename(hyperedge, "new_"+hyperedge.get_name())
      for i, node in enumerate(nodes):
         gboml_model.change_node_name_in_hyperedge(hyperedge, old_names[i], node.get_name())

   parent = gboml_model.import_node("test/test6.txt", "H")
   for node in nodes:
      gboml_model.add_sub_node(node, parent)

   for edge in edges:
      gboml_model.add_sub_hyperedge(edge, parent)

   gboml_model.redefine_parameters_from_keywords(parent, b=6)
   gboml_model.add_nodes_in_model(parent)
   gboml_model.build_model()
   solution = gboml_model.solve_cplex()
