---
title: 'GBOML: Graph-Based Optimization Modeling Language'
tags:
  - Python
  - Optimization
  - Mixed-Integer Linear Programming
  - Algebraic Modeling Language
  - Object-Oriented Modeling
  - Structured Models
  - Decomposition Methods

authors:
  - name: Bardhyl Miftari^[co-first author, corresponding author]
    orcid: 0000-0001-5334-0234
    affiliation: 1
  - name: Mathias Berger^[co-first author, corresponding author]
    orcid: 0000-0003-3081-4833
    affiliation: 1
  - name: Hatim Djelassi
    affiliation: 1
  - name: Damien Ernst
    orcid: 0000-0002-3035-8260
    affiliation: "1, 2"
affiliations:
  - name: Department of Electrical Engineering and Computer Science, University of Liège
    index: 1
  - name: LTCI, Telecom Paris, Institut Polytechnique de Paris
    index: 2
date: 21 January 2021
bibliography: references.bib
---

# Summary

The Graph-Based Optimization Modeling Language (GBOML) is a modeling language for mathematical programming enabling the easy implementation of a broad class of structured mixed-integer linear programs typically found in applications ranging from energy system planning to supply chain management. More precisely, the language is particularly well-suited for representing problems involving the optimization of discrete-time dynamical systems over a finite time horizon and possessing a block structure that can be encoded by a hierarchical hypergraph. The language combines elements of both algebraic and object-oriented modeling languages in order to facilitate problem encoding and model re-use, speed up model generation, expose problem structure to specialised solvers and simplify post-processing. The GBOML parser, which is implemented in Python, turns GBOML input files into hierarchical graph data structures representing optimization models. The associated tool provides both a command-line interface and a Python API. It also directly interfaces with a variety of open-source and commercial solvers, including structure-exploiting ones.

# Statement of need

Many planning and control problems (e.g., in the field of energy systems) can be formulated as mathematical programs. Notably, many models of practical interest can be viewed as collections of smaller models with some form of coupling between them. Such models display a natural block structure, where each block represents a small model or component.

Broadly speaking, two classes of tools can be used to implement such models, namely algebraic modeling languages (AMLs) and so-called object-oriented modeling environments (OOMEs). In short, AMLs typically allow users to compactly encode broad classes of optimization problems (e.g., mixed-integer nonlinear programs) while decoupling models and solvers. AMLs can be either stand-alone (e.g., GAMS [@GAMS] or AMPL [@AMPL]) or embedded in general-purpose programming languages, such as JuMP [@JuMP] (in Julia), Pyomo [@Pyomo] and PuLP [@PuLP] (in Python). They may also be open-source (e.g., JuMP, Pyomo and PuLP). On the other hand, OOMEs usually make it easy to construct instances of specific problems from pre-defined components. For instance, in the field of energy systems, established OOMEs include PyPSA (power flow calculations and capacity expansion planning) [@PyPSA], Calliope (multi-energy carrier capacity expansion planning) [@Calliope] or Balmorel (long-term planning and short-term operational analyses) [@Balmorel].

Unfortunately, both AMLs and OOMEs suffer from several drawbacks. More precisely, AMLs rarely provide language constructs to represent the block structure in a model and typically fail to take advantage of it, although this may be used to simplify problem encoding (e.g., by treating blocks as independent objects), enable model re-use (e.g., by allowing the import of model components), speed up model generation (e.g., by parallelising block generation) and facilitate the use of structure-exploiting solution algorithms. Extensions to established AMLs were proposed to address some of these concerns, such as StructJuMP [@StructJuMP], PySP [@PySP] and SML [@SML] (extending JuMP, Pyomo and AMPL, respectively). However, these extensions were usually designed with the primary aim of handling very specific problem structures (e.g., dual block angular structures found in stochastic linear  programming models). On the other hand, OOMEs typically lack expressiveness and adding components is often cumbersome. Furthermore, they very often rely on established AMLs themselves and thus automatically inherit any shortcomings of the AML on top of which they are built (e.g., it may not be open-source).

The tools that appear closest in spirit to our own are the recent SMS++ modeling framework [@SMSpp] and Plasmo.jl [@Plasmo] (an extension of JuMP). The former makes it possible to implement fairly general block-structured models and aims to ease the development and deployment of advanced structure-exploiting algorithms. The latter relies on a graph abstraction of optimization models to enable modular model construction, partitioning and the use of structure-exploiting algorithms.

Against this backdrop, GBOML was designed to blend and natively support some key features of AMLs and OOMEs. Notably, it was built with the following goals in mind:

- being open-source and stand-alone
- allowing any mixed-integer linear program to be represented
- enabling any hierarchical block structure to be exposed and exploited
- facilitating the encoding and construction of time-indexed models
- allowing low-level model encoding to be close to mathematical notation
- making it easy to re-use and combine components and models
- interfacing with commercial and open-source solvers, including structure-exploiting ones

An early version of the tool was used in a research article studying the economics of carbon-neutral fuel production in remote areas where renewable resources are abundant [@RemoteHub]. The tool is also used in the context of a research project focusing on the design of the future Belgian energy system.

# Example

Next, we describe a short example illustrating how GBOML works. First, a model must be encoded in a GBOML input file. An input file implementing a stylised microgrid investment planning problem is shown below.

```
#TIMEHORIZON
T = 8760; // planning horizon (hours)

#NODE SOLAR_PV
#PARAMETERS
capex = 600; // annualised capital expenditure per unit capacity
capacity_factor = import "pv_gen.csv"; // normalised generation profile
#VARIABLES
internal: capacity; // capacity of solar PV plant
external: power[T]; // power output of solar PV plant
#CONSTRAINTS
capacity >= 0;
power[t] >= 0;
power[t] <= capacity_factor[t] * capacity;
#OBJECTIVES
min: capex * capacity;

#NODE BATTERY
#PARAMETERS
capex = 150; // annualised capital expenditure per unit capacity
#VARIABLES
internal: capacity; // energy capacity of battery storage system
internal: energy[T]; // energy stored in battery storage system
external: power[T]; // power flow in/out of battery storage system
#CONSTRAINTS
capacity >= 0;
energy[t] >= 0;
energy[t] <= capacity;
energy[t+1] == energy[t] + power[t];
#OBJECTIVES
min: capex * capacity;

#HYPEREDGE POWER_BALANCE
#PARAMETERS
electrical_load = import "electrical_load.csv";
#CONSTRAINTS
SOLAR_PV.power[t] == electrical_load[t] + BATTERY.power[t];
```

The optimization horizon is defined at the beginning of the GBOML input file. Two node blocks then define the solar photovoltaic (PV) and battery storage system models, respectively. Each node has its own parameters, variables, constraints and objectives. Finally, a hyperedge block is used to ensure that power flows in the microgrid are balanced and the electricity demand is satisfied.

Then, the command-line interface or the Python API may be used to generate the model and solve it. Model generation can be parallelised based on the block structure provided by the user and models can be passed to open-source or commercial solvers. Direct access to several solver APIs is provided, allowing users to tune algorithm parameters and query complementary information (e.g., dual variables, slacks or basis ranges, when available).

Finally, results are retrieved and can be either printed to file or used directly in Python. Two file formats are supported at the time of writing, namely CSV and JSON.

The full GBOML syntax is described in the online documentation, along with advanced features such as model imports and hierarchical model construction as well as solver options. The files required to run the example above are available in the GBOML repository.

# Acknowledgements

The authors gratefully acknowledge the support of the Federal Government of Belgium through its Energy Transition Fund and the INTEGRATION project. The authors would also like to thank Adrien Bolland for his help with an early version of the documentation, Jocelyn Mbenoun for testing some early features of the tool, as well as Ghislain Detienne and Thierry Deschuyteneer for constructive discussions.

# References
