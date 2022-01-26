---
title: 'GBOML: Graph-Based Optimization Modeling Language'
authors:
  - name: Bardhyl Miftari^[co-first author, corresponding author]
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

The Graph-Based Optimization Modeling Language (GBOML) is a modeling language for mathematical programming enabling the easy implementation of a broad class of structured mixed-integer linear programs typically found in applications ranging from energy system planning to supply chain management. More precisely, the language is particularly well-suited for representing problems involving the optimization of discrete-time dynamical systems over a finite time horizon and possessing a block structure that can be encoded by a hierarchical hypergraph. The language combines elements of both algebraic and object-oriented modeling languages in order to facilitate problem encoding and model re-use, speed up model generation, expose problem structure to specialised solvers and simplify post-processing. The GBOML parser, which is implemented in Python, turns GBOML input files into hierarchical graph data structures representing optimization models. The associated tool provides both a command-line interface and a Python API to construct models, and directly interfaces with a variety of open source and commercial solvers, including structure-exploiting ones.

# Statement of need

Many planning and control problems (e.g., in the field of energy systems) can be formulated as mathematical programs and the resulting models often possess special structure. Broadly speaking, two classes of tools can be used to implement such models, namely algebraic modeling languages (AMLs) and so-called application-specific modeling frameworks (ASMFs). On the one hand, AMLs usually make it possible to encode problems in a way that is close to mathematical notation. In addition, they are usually very expressive (e.g., any mixed-integer nonlinear program can be encoded) and application-agnostic, and they also interface with a variety of solvers. AMLs can either be stand-alone, such as GAMS [@GAMS] or AMPL [@AMPL], or they may be embedded in general-purpose programming languages, such as JuMP [@JuMP] (in Julia) or Pyomo [@Pyomo] and PuLP [@PuLP] (both in Python). Some of them are also open source (e.g., JuMP, Pyomo and PuLP). In short, AMLs enable users to compactly encode broad classes of optimization problems while decoupling models and solvers. On the other hand, ASMFs focus on a specific application (e.g., capacity expansion planning) and are best understood as modeling frameworks facilitating the construction of instances of a specific problem. As such, ASMFs often provide a set of pre-defined components that can be imported to build a model, along with advanced data pre- and post-processing features tailored to the application at hand. In summary, ASMFs enable the easy and modular construction of specific problem instances. In the field of energy systems, which is a particularly relevant application area for GBOML, established ASMFs include PyPSA (power flow calculations and capacity expansion planning, among others) [@PyPSA], PowerModels.jl (analysis and comparison of optimal power flow formulations) [@PowerModels], Calliope (multi-energy carrier capacity expansion planning) [@Calliope], Dispa-SET (economic dispatch and unit commitment) [@DispaSET], Balmorel (long-term planning and short-term operational analyses) [@Balmorel] and OSeMOSYS (long-run energy planning) [@OSeMOSYS].

Unfortunately, both AMLs and ASMFs suffer from several drawbacks. More precisely, AMLs usually lack modularity. In particular, most AMLs fail to exploit the separable structure that may exist in a model (e.g., to enable collaborative encoding or speed up model generation by parallelising it) or expose it for use by specialised solvers. Extensions to established AMLs were proposed to address the latter concerns, such as StructJuMP [@StructJuMP], BlockDecomposition.jl [@BlockDecomposition] (both being extensions of JuMP), PySP [@PySP] for Pyomo and SML [@SML] for AMPL. However, these extensions were usually designed with the primary aim of exposing very specific problem structures (e.g., dual block angular structures found in stochastic linear  programming models) or facilitating the use of specific structure-exploiting algorithms (e.g., branch-price-and-cut). On the other hand, ASMFs typically lack expressiveness and adding components is often cumbersome. Furthermore, they usually rely on established AMLs themselves, which implies that they automatically inherit any shortcomings of the specific AML on top of which they are built (e.g., some AMLs are notoriously slow or may not be open source). The tools that appear closest in spirit to our own are the recent SMS++ modeling framework [@SMSpp] and Plasmo.jl [@Plasmo] (an extension of JuMP). Although the source code of SMS++ is publicly available, to the authors' best knowledge, documentation and examples are scarce at the time of writing. Plasmo seems to be under development and appears only partially documented.

In order to address some of these shortcomings, GBOML was designed with the following objectives in mind:

- allowing any mixed-integer linear program to be represented
- enabling any hierarchical block structure to be exposed and exploited
- facilitating the encoding and construction of time-indexed models
- allowing low-level model encoding to be close to mathematical notation
- making it easy to re-use and combine components and models
- interfacing with commercial and open source solvers, including structure-exploiting ones

The GBOML workflow is as follows. Models are first encoded by a user in GBOML input files. Then, these files are parsed with the GBOML parser, which is implemented in Python. A command-line interface as well as a Python API are available to work with models, which makes it possible to cater to a broad audience including both users with little programming experience and users who are proficient in Python. Model generation can also be parallelised based on the structure provided by the user. Models are then passed to open source or commercial solvers. Direct access to solver APIs is also provided, allowing users to tune algorithm parameters and retrieve complementary information (e.g., dual variables, slacks or basis ranges, when available). Finally, results are retrieved and can be either used directly in Python or printed to file. Two file formats are currently supported, namely CSV and JSON.

An early version of the tool was used in a research article studying the economics of carbon-neutral fuel production in remote areas where renewable resources are abundant [@RemoteHub]. The tool is also used in the context of a research project focusing on the design of the future Belgian energy system.

# Acknowledgements

The authors gratefully acknowledge the support of the Federal Government of Belgium through its Energy Transition Fund and the INTEGRATION project. The authors would also like to thank Adrien Bolland for his help with an early version of the documentation, Jocelyn Mbenoun for testing some early features of the tool, as well as Ghislain Detienne and Thierry Deschuyteneer for constructive discussions.

# References
