*GBOML: Graph-Based Optimization Modeling Language*

---

## Contents

- [About](#about)
- [Quick start](#quick-start)
- [Documentation](#documentation)
- [Community guidelines](#community-guidelines)
- [Citing GBOML](#citing-GBOML)
- [License](#license)

---

## About

The Graph-Based Optimization Modeling Language (GBOML) is a modeling language for mathematical programming enabling the easy implementation of a broad class of structured mixed-integer linear programs typically found in applications ranging from energy system planning to supply chain management. More precisely, the language is particularly well-suited for representing problems involving the optimization of discrete-time dynamical systems over a finite time horizon and possessing a block structure that can be encoded by a hierarchical hypergraph. The language combines elements of both algebraic and object-oriented modeling languages in order to facilitate problem encoding and model re-use, speed up model generation, expose problem structure to specialised solvers and simplify post-processing. The GBOML parser, which is implemented in Python, turns GBOML input files into hierarchical graph data structures representing optimization models. The associated tool provides both a command-line interface and a Python API to construct models, and directly interfaces with a variety of open source and commercial solvers, including structure-exploiting ones.

## Quick start

GBOML has been tested on Windows, macOS and Linux. The simplest way to install it is via the *pip* package manager in a terminal window:

    pip install gboml

Please refer to the online documentation for more [information on how to install GBOML](https://gboml.readthedocs.io/en/latest/installation.html). Note that optimization solvers are also required to solve GBOML models and installation instructions are also provided in the online documentation.

Several examples are provided in this repository ([in the examples directory](examples/)) and explained in the [online documentation](https://gboml.readthedocs.io/en/latest/).

## Documentation

Documentation is available on Read the Docs:

* [Read the documentation online](https://gboml.readthedocs.io/en/latest/)

## Community guidelines

To contribute changes:

1. Fork the project on Gitlab
2. Create a feature branch to work on in your fork (`git checkout -b new-feature`)
3. Commit your changes to the feature branch
4. Push the branch to Gitlab (`git push origin my-new-feature`)
5. On Gitlab, create a new pull request from the feature branch

Issues and questions shall be reported in the [issues directory](https://gitlab.uliege.be/smart_grids/public/gboml/-/issues).

## Citing GBOML

An early version of the GBOML framework was introduced in [a recent paper](https://www.frontiersin.org/articles/10.3389/fenrg.2021.671279/full). GBOML has also been submitted for review to the Journal of Open Source Software.

## License
Copyright (C) since 2020 Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst, University of Liege .   Licensed under the MIT License (see LICENSE file).
