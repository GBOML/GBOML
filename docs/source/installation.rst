Installation
============

Two installation options are currently available. First, GBOML can be installed via the pip package manager and the Python Package Index (PyPI). Second, GBOML can be installed manually by cloning the git repository and installing the requirements.
In addition, solvers must be installed separately, as described below.

Installation via pip and PyPI
-----------------------------

GBOML can be installed via pip and the Python Package Index by typing the following commands in a terminal window:

.. code-block:: bash

	pip install gboml

All dependencies (numpy, scipy and ply) will be automatically installed and the package should be ready for use.

Manual Installation
-------------------

The git repository can be found `here <https://gitlab.uliege.be/smart_grids/public/gboml>`_. The repository can be cloned by typing the following commands in a terminal window:

.. code-block:: bash

	git clone https://gitlab.uliege.be/smart_grids/public/gboml

Then, a local installation can be performed by typing the following commands in a terminal window:

.. code-block:: bash

	pip install .

If you only want GBOML as an uninstalled package, installing the requirements can be performed by typing the following commands:

.. code-block:: bash

	pip install -r requirements.txt

Installing Solvers
------------------

GBOML currently interfaces with Gurobi, CPLEX, Xpress, Cbc/Clp and DSP. Only one of these is required to solve a GBOML model. Gurobi, CPLEX and Xpress are commercial solvers, while Cbc/Clp is an open-source solver. DSP is an experimental open-source project relying on Gurobi, CPLEX and SCIP to implement generic structure-exploiting algorithms (e.g., Dantzig-Wolfe, dual and Benders decompositions).

Gurobi
~~~~~~

To use Gurobi, you must first install it. Instructions can be found `here <https://www.gurobi.com/documentation/9.5/quickstart_windows/software_installation_guid.html>`_. Once the solver is installed, the Python API can be downloaded by typing the following commands in a terminal window:

.. code-block:: bash

	python -m pip install -i https://pypi.gurobi.com gurobipy

Other installation options can be found in `this post <https://support.gurobi.com/hc/en-us/articles/360044290292-How-do-I-install-Gurobi-for-Python->`_. Note that a license is also required to use Gurobi. Free licenses can be requested for academics, as discussed in the following `post <https://www.gurobi.com/academia/academic-program-and-licenses/>`_.

CPLEX
~~~~~
To use CPLEX, you must first install it. Instructions can be found `here <https://www.ibm.com/support/pages/downloading-ibm-ilog-cplex-optimization-studio-2010>`_. Once the solver is installed, the Python API can be downloaded by typing the following commands in a terminal window:

.. code-block:: bash

	pip install cplex

Note that a license is also required to use CPLEX. Licenses can be obtained for free for academics, as discussed in the following `post <https://www.ibm.com/support/pages/ibm-ilog-optimization-academic-initiative>`_.

Xpress
~~~~~~
To use Xpress, you must first install it. Instructions can be found `here <https://www.fico.com/fico-xpress-optimization/docs/latest/insight_quick_install/GUID-2D3D6579-9CCA-4605-8C00-E91B6FB846EB.html>`_. Once the solver is installed, the Python API can be downloaded by typing the following commands in a terminal window:

.. code-block:: bash

	pip install xpress

Additional information can be found `here <https://www.fico.com/fico-xpress-optimization/docs/latest/solver/optimizer/python/HTML/chIntro_sec_secInstall.html>`_. Note that a license is also required to use Xpress.

Cbc/Clp
~~~~~~~

To use Cbc or Clp, you must first install them. Instructions can be found `here <https://github.com/coin-or/Cbc>`_. The CyLP package is used to interface with the solver. This package can be installed by typing the following commands in a terminal window:

.. code-block:: bash

	pip install cylp

DSP
~~~

To use DSP, you must first install it. At present, DSP developers recommend installing it on a Mac or Linux machine. Installing DSP with the Windows Subsystem Linux UBUNTU 18.04 distribution was tested and found to work too.

The recommended installation steps work as follows. First, the DSP repository must be cloned into a directory of choice. This can be achieved by creating a directory named, e.g., *your_DSP_directory*:

.. code-block:: bash

	mkdir your_DSP_directory
	cd your_DSP_directory

and cloning the DSP repository recursively:

.. code-block:: bash

	git clone --recursive https://github.com/Argonne-National-Laboratory/DSP.git

Then, the absolute paths of the directories storing the libraries and header files of the solvers used to build DSP (e.g., Gurobi, CPLEX or SCIP) must be specified in a file named :math:`\texttt{UserConfig.cmake}`, which must be placed in the cloned DSP directory.
Note that these paths must be consistent with that of the directory in which the solver was installed in the first place. For example, on Mac, CPLEX library files may be stored in */Applications/CPLEX_Studio1210/cplex/lib/x86-64_osx/static_pic*, while header files
may be stored in */Applications/CPLEX_Studio1210/cplex/include/ilcplex*. Gurobi libraries and header files may be stored in */Library/gurobi903/mac64/lib* and */Library/gurobi903/mac64/include*, respectively. In addition, it may sometimes be necessary to also add some of these libraries and DSP dependencies
on the library path (e.g., by setting the value of the DYLD_LIBRARY_PATH environment variable in your bash profile on Mac) prior to proceeding to the build stage.

The next installation steps make use of `cmake <https://cmake.org/install/>`_ and make to build the DSP executable and library. Once cmake is installed, the following commands can be typed in a terminal window, starting in the cloned DSP directory:

.. code-block:: bash

  mkdir build
  cd build
  cmake ..
  make

If the make worked properly, an executable called runDsp and a shared library named libDsp should be created in the *src* subfolder of the build directory. Additional information can be found `here <https://github.com/Argonne-National-Laboratory/DSP/blob/master/docs/install.md>`_.
