# Towards CO2 Valorization in a multi remote renewable energy hub framework

Repository for our scientific paper results: https://arxiv.org/abs/2303.09454 .


# Installation

First you need to setup your conda environment.

```conda env create -f environment.yml```

You can also use any management of environment you want the installed libraries are standard:
matplotlib, numpy, pandas. 

The only special library is gboml. You can find the documentation and installation guide here:
https://gboml.readthedocs.io/en/latest/


# How to use the code

In order to reproduce the results obtained in the article run:

```python3 main.py -sc $num_scenario -y 2```

There are 5 scenarios from 1 to 5. 

Therefore, ```$num_scenario \in {1, 2, 3, 4, 5}```

# Cite
Please, if you use this code in your work consider citing https://arxiv.org/abs/2303.09454 : 

@misc{dachet2023co2,
      title={Towards CO2 valorization in a multi remote renewable energy hub framework}, 
      author={Victor Dachet and Amina Benzerga and Raphaël Fonteneau and Damien Ernst},
      year={2023},
      eprint={2303.09454},
      archivePrefix={arXiv},
      primaryClass={math.OC}
}



