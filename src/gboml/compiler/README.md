*GBOML: Graph-Based Optimization Modeling Language*

---
## Contents of files
The source code of the GBOML compiler is divided in 8 parts : 
- The classes contain the classes used in the GBOML syntax tree
- The PLY source directory to remove the PLY dependency from https://github.com/dabeaz/ply
- gboml_compiler.py defines the general function related to compiling a gboml file
- gboml_lexer.py defines the GBOML lexer
- gboml_parser.py defines the GBOML parser and its grammar
- gboml_semantic.py contains all the functions related to the semantic checking
- gboml_matrix_generation containts all the functions related to transforming the syntax tree into matrices
- utils.py contains utility functions that are used through-out the code.