# Towards CO2 Valorization in a multi remote renewable energy hub framework

A newer version of this paper and software is available here: 
https://github.com/VicD1999/towards_co2 .

Repository for our scientific paper results: https://arxiv.org/abs/2303.09454 or https://orbi.uliege.be/handle/2268/301033 .


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
Please, if you use this code in your work consider citing https://arxiv.org/abs/2303.09454 or https://orbi.uliege.be/handle/2268/301033 : 

@inproceedings{ORBi-f72d55b3-ab04-47a6-b325-b26f59e8335a,
	AUTHOR = {Dachet, Victor and Benzerga, Amina and Fonteneau, Raphaël and Ernst, Damien},
	TITLE = {Towards CO2 valorization in a multi remote renewable energy hub  framework},
	LANGUAGE = {English},
	YEAR = {17 March 2023},
	DOI = {10.52202/069564-0172},
	LOCATION = {Las Palmas, Spain},
	ABSTRACT = {In this paper, we propose a multi-RREH (Remote Renewable Energy Hub) based
		optimization framework. This framework allows a valorization of CO2 using
		carbon capture technologies. This valorization is grounded on the idea that CO2
		gathered from the atmosphere or post combustion can be combined with hydrogen
		to produce synthetic methane. The hydrogen is obtained from water electrolysis
		using renewable energy (RE). Such renewable energy is generated in RREHs, which
		are locations where RE is cheap and abundant (e.g., solar PV in the Sahara
		Desert, or wind in Greenland). We instantiate our framework on a case study
		focusing on Belgium and 2 RREHs, and we conduct a techno-economic analysis.
		This analysis highlights the key role played by the cost of the two main carbon
		capture technologies: Post Combustion Carbon Capture (PCCC) and Direct Air
		Capture (DAC). In addition, we use our framework to derive a carbon price
		threshold above which carbon capture technologies may start playing a pivotal
		role in the decarbonation process of our industries. For example, this price
		threshold may give relevant information for calibrating the EU Emission Trading
		System so as to trigger the emergence of the multi-RREH.}
}



