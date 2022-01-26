Identifiers
===========

Identifiers are used to name different kinds of language objects such as nodes, hyperedges or variables. Identifiers may contain letters, numbers, underscores, and dollar signs but must begin with a letter or an underscore.
Accordingly, the following identifiers are all valid,

.. math::
    \texttt{mynode1}, \qquad \texttt{_SolarPlant_2}, \qquad \texttt{HydroStorage_\$}.

Besides these lexical requirements, identifiers must also be unique in their respective scope. Hence, no two nodes may have the same identifier since this would prohibit the unambiguous identification of a particular node.
Similarly, variables and parameters may not have the same identifier as a node or other variables and parameters belonging to the same node.
However, the same identifier may be re-used to define variables or parameters that belong to different nodes.
