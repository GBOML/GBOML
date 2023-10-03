
This directory contains the GBOML models used in the paper 

> **Synthetic methane for closing the carbon loop: Comparative study of three
carbon sources for remote carbon-neutral fuel synthetization**
>
> [Michaël Fonder](https://www.uliege.be/cms/c_9054334/fr/repertoire?uid=u225873), Pierre Counotte, [Victor Dachet](https://www.uliege.be/cms/c_9054334/fr/repertoire?uid=u234824), Jehan de Séjournet, and [Damien Ernst](https://www.uliege.be/cms/c_9054334/fr/repertoire?uid=u030242)


In this repository, we use the following denomination for our three carbon sourcing configurations:
* scenario 1 : DAC in Morocco
* scenario 2 : PCCC in Morocco
* scenario 3 : PCCC in Belgium + DAC in Morocco

The sizing of the RREH can be optimized for all the configurations described in the paper by running:
```shell
python run_models.py
```

Most of the data presented in the tables of the paper are derived from the output json file generated for each configuration. Computing the unit cost of each commodity requires some model alterations and cannot be simply derived from these data. To get the commodity cost for our models, we provide the [`commodity_costs.py`](commodity_costs.py) script which can be run to get the table of the commodity costs:
```shell
python commodity_cost.py
```
Output files will be located in a new `commodity_cost_results` directory.

## Dependencies

You need a working installation of GBOML with the python API, and of Gurobi to use the scripts given in this repository. GBOML models can be optimized individually with any working install of GBOML.

## Citation

If you use our work in your research, please consider citing our paper:

```
@article{Fonder2023Synthetic,
  title     = {Synthetic methane for closing the carbon loop: Comparative study of three carbon sources for remote carbon-neutral fuel synthetization},
  author    = {Fonder, Micha\"el and Counotte, Pierre and Dachet, Victor and De S\'ejournet, Jehan and Ernst, Damien},
  booktitle = {arXiv},
  month     = {October},
  year      = {2023}
}
```

