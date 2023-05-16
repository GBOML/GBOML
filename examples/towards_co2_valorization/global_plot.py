import os
import sys
import json
import csv
import calendar
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from analysis import MakeMeReadable

import pandas as pd

def create_cost_csv(ls:list):

    ls_prices = []
    NZ_nodes = []
    for f in ls:
        filename = f"Results/" + f

        dico = {}
        with open(filename, "r") as fp:
            dico = json.load(fp)

        d = MakeMeReadable(dico)

        ls_nodes = list(d.model.nodes.keys())
        ls_nodes.remove("PROD_CO2")

        if len(NZ_nodes) < 1:
            NZ_nodes = list(map(lambda string: string if string[-3:] not in ["_GR", "_BE"] else None, ls_nodes))
            NZ_nodes = list(filter(lambda x: x not in [None, "PCCC", "PROD_CO2", "CO2_EXPORT", "PCCC_CCGT", "CCGT_BE", "LIQUEFIED_METHANE_STORAGE_DESTINATION","LIQUEFIED_METHANE_REGASIFICATION",], NZ_nodes))

        # print(ls_nodes)
        def f(x):
            return x, cost_rreh([x], dico)

        ls_prices_decomposition = list(map(f, ls_nodes))
        ls_prices.append(ls_prices_decomposition)

        indices, ls_prices[0] = zip(*sorted(enumerate(ls_prices[0]), key=lambda x : x[1][1], reverse=True))

    for i in range(1, len(ls_prices)):
        ls_prices[i] = list(sorted(ls_prices[i], key=lambda j: indices.index(ls_prices[i].index(j))))

        if len(ls_prices[i]) == 25:
            ls_prices[i] = list(ls_prices[i]) + list(zip(NZ_nodes, [0] * len(NZ_nodes)))
    ls_prices[0] = list(ls_prices[0])

    for i in range(len(ls_prices)):
        ls_prices[i] = list(sorted(ls_prices[i], key=lambda x: x[0]))

    header = list(map(lambda x: x[0], ls_prices[0]))
    data = [list(map(lambda x: x[1], ls_prices[i])) for i in range(len(ls_prices))]

    with open('cost.csv', 'w', encoding='UTF8') as f:
        writer = csv.writer(f)
        # write the header
        writer.writerow(header)
        # write the data
        for i in range(len(data)):
            writer.writerow(data[i])

    return ls_prices

def cost_rreh(ls:list, dico:dict):
    if len(ls) == 0:
        return 0.0

    cost = 0

    for ele in ls:
        try:
            cost += np.sum(dico["solution"]["elements"][ele]["objectives"]["unnamed"])
        except:
            for e in dico["solution"]["elements"][ele]["objectives"]["named"].values():
                cost += e
    
    return cost

def cost_per_cluster(ls):
    """
    arguments:
    ----------
        ls: a list with names of json file to explore 
    """

    cost_sc_nz = []
    cost_sc_gr = []
    cost_sc_be = []

    for f in ls:
        filename = f"Results/" + f
        # print(filename)

        dico = {}
        with open(filename, "r") as fp:
            dico = json.load(fp)

        d = MakeMeReadable(dico)
        
        # COST PER CLUSTER ANALYSIS
        ls_nodes = list(d.model.nodes.keys())

        try:
            GR_nodes = list(map(lambda string: string if string[-3:] == "_GR" else None, ls_nodes))
        except:
            GR_nodes = []
        NZ_nodes = list(map(lambda string: string if string[-3:] not in ["_GR", "_BE"] else None, ls_nodes))
        BE_nodes = list(map(lambda string: string if string[-3:] == "_BE" or string in ["PCCC_CCGT", "PCCC", "CO2_EXPORT", "LIQUEFIED_METHANE_STORAGE_DESTINATION","LIQUEFIED_METHANE_REGASIFICATION"] else None, ls_nodes))

        try:
            GR_nodes = list(filter(lambda x: x not in [None, "PCCC", "PROD_CO2", "CO2_EXPORT"], GR_nodes))
        except:
            GR_nodes = []
        NZ_nodes = list(filter(lambda x: x not in [None, "PCCC", "PROD_CO2", "CO2_EXPORT", "PCCC_CCGT", "CCGT_BE", "LIQUEFIED_METHANE_STORAGE_DESTINATION","LIQUEFIED_METHANE_REGASIFICATION",], NZ_nodes))
        BE_nodes = list(filter(lambda x: x not in [None, "PROD_CO2"], BE_nodes))

        cost_NZ = cost_rreh(NZ_nodes, dico)
        cost_GR = cost_rreh(GR_nodes, dico)
        cost_BE = cost_rreh(BE_nodes, dico)

        cost_sc_nz.append(cost_NZ)
        cost_sc_gr.append(cost_GR)
        cost_sc_be.append(cost_BE)


    return cost_sc_nz, cost_sc_gr, cost_sc_be


def blackout():
    ls = ['load_factor_pv.csv',
         'load_factor_won.csv',
         'load_factor_woff.csv',
         'demand_ng.csv',
         'demand_el.csv',
         'carrier_schedule.csv'
         ]

    legend = ['Load factor pv',
         'Load factor wind onshore',
         'Load factor wind offshore',
         'Demand natural gas',
         'Demand electricity',
         'Carrier schedule'
         ]

    fontsize = 12

    # days = ["16h", "17h", "18h", "19h"]
    days = [f"{ (8 + i)%24 }h" for i in range(0,20)]

    fig, ax1 = plt.subplots()

    for i, f in enumerate(ls):
        df = pd.read_csv(f"data/{f}", header=None)
        if f == 'carrier_schedule.csv':
            ax1.scatter(np.array(list(range(440,460))), df.iloc[440:460] / df.max(), label=legend[i])
        else:
            ax1.plot(df.iloc[440:460] / df.max(), label=legend[i])
        
    # Set the x-axis labels
    freq = 5
    ax1.set_xticks(range(440, 460, freq))
    ax1.set_xticklabels(days[::freq])
    ax1.set_xlabel("18th day in January", fontsize=fontsize)
    ax1.set_ylim(-0.1, 1.1)
    ax1.set_ylabel('Normalized Energy Demand/Power Output', fontsize=fontsize)
    ax1.grid()
    # Move the legend outside of the plot
    ax1.legend(loc=(0.5, 0.25))

    # Add a new y-axis on the right
    ax2 = ax1.twinx()
    ax2.set_ylim(-0.1, 1.1)
    ax2.set_yticks([0, 1])
    ax2.set_ylabel("Availability of a CH4 Carrier", fontsize=fontsize)
    # ax2.plot(range(440, 460), carrier_schedule_capacity_fraction(), label="Carrier schedule capacity", color="purple")
    # ax2.legend(loc="upper left")

    plt.savefig("Figures/blackout.pdf", dpi=1200)
    plt.close()


def energy_demand():
    def daily_sum(ts):
        elec = np.array(ts[0])
        elec = elec.reshape((elec.shape[0]//24, 24))
        sum_elec = np.sum(elec, axis=1)
        
        return sum_elec

    df_elec = pd.read_csv("data/demand_el.csv", header=None)
    df_gas = pd.read_csv("data/demand_ng.csv", header=None)

    sum_elec = daily_sum(df_elec)
    sum_gas = daily_sum(df_gas)

    years = 2

    month_names = [calendar.month_name[i] for i in range(1, 13)]
    month_names = list(map(lambda x: x + " 2015", month_names)) + list(map(lambda x: x + " 2016", month_names)) + ['']

    # month_names = [calendar.month_name[i] for i in range(1, 13)] * years + [''] # add a placeholder string

    tmp = (sum_elec.shape[0] // 3) * years
    months= [x for x in range(0,tmp)]

    days = [x for x in range(tmp)]

    plt.figure(figsize=(10,8))

    color1, color2 = 'steelblue', 'lightcoral'

    linewidth = 2

    plt.plot([],[], color=color1, label='Electricity', linewidth=linewidth)
    plt.plot([],[], color=color2, label='Gas', linewidth=linewidth)

    plt.stackplot(days, sum_elec[:tmp], colors=[color1], alpha=1., linewidth=linewidth)
    plt.stackplot(days, sum_gas[:tmp], colors=[color2], alpha=.7, linewidth=linewidth)

    plt.legend()
    plt.xlim(0, tmp)
    freq = 4
    plt.xticks(months[::30*freq], month_names[::freq], rotation=0)

    plt.ylabel('Energy demand [GWh/day]')

    plt.axhline(color='black', linewidth=1)

    plt.savefig("Figures/energy_demand.pdf", dpi=1200)

    plt.close()

def price_per_scenario_cluster(ls:list):

    cost_sc_nz, cost_sc_gr, cost_sc_be = cost_per_cluster(ls)

    N = 5
    cost_sc_nz = np.array(cost_sc_nz)
    cost_sc_gr = np.array(cost_sc_gr)
    cost_sc_be = np.array(cost_sc_be)

    xtickx_labels = [f"Scenario {i}" for i in range(1, N+1)]

    ind = np.arange(N)
    width = 0.35
    zorder = 0

    fig, ax = plt.subplots(figsize=(10, 7))

    p1 = ax.bar(ind, cost_sc_be, width, zorder=2)
    p2 = ax.bar(ind, cost_sc_nz, width, bottom=cost_sc_be, zorder=2)
    p3 = ax.bar(ind, cost_sc_gr, width, bottom=cost_sc_be + cost_sc_nz, zorder=2)

    ax.set_xticks(ind)
    ax.set_xticklabels(xtickx_labels)
    ax.set_yticks(np.arange(0, 120000, 10000))

    ax.grid(axis='y', zorder=1)  # set the zorder of the grid to a lower value than the bars
    ax.legend((p1[0], p2[0], p3[0]), ('BE', 'DZ', 'GL'))

    plt.savefig("Figures/price_per_scenario_cluster.pdf", dpi=1200)
    plt.close()

def costs_subplot(ls:list):

    cost_sc_nz, cost_sc_gr, cost_sc_be = cost_per_cluster(ls)

    ls_flex = ['BATTERY_STORAGE', 'BATTERY_STORAGE_GR', 'CARBON_DIOXIDE_STORAGE', 'HYDROGEN_STORAGE', 'HYDROGEN_STORAGE_GR', 
       'LIQUEFIED_METHANE_STORAGE_DESTINATION','LIQUEFIED_METHANE_STORAGE_HUB', 'LIQUEFIED_METHANE_STORAGE_HUB_GR',
          'WATER_STORAGE', 'WATER_STORAGE_GR']

    ls_co2 = ['CARBON_DIOXIDE_STORAGE_BE', 'CARBON_DIOXIDE_STORAGE_GR', 'CO2_EXPORT','DIRECT_AIR_CAPTURE_PLANTS','DIRECT_AIR_CAPTURE_PLANTS_GR','PCCC','PCCC_CCGT', 'CARRIER_CO2','CARRIER_CO2_GR']
    ls_power = ['CCGT_BE', 'ENERGY_DEMAND_BE', 'SOLAR_BE', 'SOLAR_PV_PLANTS', 'WIND_OFFSHORE_BE', 'WIND_ONSHORE_BE','WIND_PLANTS', 'WIND_PLANTS_GR']
    ls_units = ['DESALINATION_PLANTS','DESALINATION_PLANTS_GR','ELECTROLYSIS_PLANTS','ELECTROLYSIS_PLANTS_GR', 'LIQUEFIED_METHANE_REGASIFICATION', 'METHANATION_PLANTS', 'METHANATION_PLANTS_GR','METHANE_LIQUEFACTION_PLANTS', 'METHANE_LIQUEFACTION_PLANTS_GR']
    ls_transport = ['LIQUEFIED_METHANE_CARRIERS','LIQUEFIED_METHANE_CARRIERS_GR', 'HVDC', 'HVDC_GR']

    def cost_from_df(ls, df):
        cost = 0
        for ele in ls:
            cost += df[ele]
        return cost

    ls_units = [ls_flex,
            ls_co2,
            ls_power,
            ls_units,
            ls_transport]

    costs = np.zeros((5, len(ls_units)))

    df = pd.read_csv("cost.csv")
    for j, ls in enumerate(ls_units):
        # print(j, ls, "\n")
        costs[:,j] = cost_from_df(ls, df).values
    
    # First plot
    N = 5
    ytickx_labels = [f"Scenario {i}" for i in range(1, N+1)]

    ind = np.arange(N)
    width = 0.35
    zorder = 0
    fontsize = 14

    fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(15, 7))

    cost_sc_nz = np.array(cost_sc_nz)
    cost_sc_gr = np.array(cost_sc_gr)
    cost_sc_be = np.array(cost_sc_be)

    ytickx_labels = [f"Scenario {i}" for i in range(1, N+1)]

    p1 = axs[0].barh(ind, cost_sc_be, width, zorder=2)
    p2 = axs[0].barh(ind, cost_sc_nz, width, left=cost_sc_be, zorder=2)
    p3 = axs[0].barh(ind, cost_sc_gr, width, left=cost_sc_be + cost_sc_nz, zorder=2)

    axs[0].set_yticks(ind)
    axs[0].set_yticklabels(ytickx_labels, fontsize=fontsize)
    axs[0].set_xticks(np.arange(0, 120000, 20_000), )
    axs[0].grid(axis='x', zorder=1)  # set the zorder of the grid to a lower value than the bars
    axs[0].legend((p1[0], p2[0], p3[0]), ('BE', 'DZ', 'GL'), fontsize=fontsize, frameon=True)
    axs[0].set_xlabel("(a)", fontsize=fontsize)

    # Increase thickness of x-axis labels and legend
    axs[0].tick_params(axis='x', which='major', width=2, length=7, labelsize=fontsize)
    axs[0].legend((p1[0], p2[0], p3[0]), ('BE', 'DZ', 'GL'), fontsize=fontsize, frameon=True, handlelength=1.5, loc="center right")



    # Second plot
    ps = []

    for j in range(len(ls_units)):
        ps.append(axs[1].barh(ind, costs[:,j], width, left=np.sum(costs[:,:j], axis=1), zorder=2))

    axs[1].set_yticks(ind)
    axs[1].set_yticklabels(ytickx_labels, fontsize=fontsize)
    axs[1].set_xticks(np.arange(0, 120000, 20_000), fontsize=fontsize)
    axs[1].set_xlabel("(b)", fontsize=fontsize)

    axs[1].grid(axis='x', zorder=1)  # set the zorder of the grid to a lower value than the bars
    # axs[1].legend(map(lambda x: x[0], ps), ["Flexibility", "CO2 infra", "Power assets", "Conversion", "CH4 transport"], fontsize=fontsize, frameon=True)

    # Increase thickness of x-axis labels and legend
    axs[1].tick_params(axis='x', which='major', width=2, length=7, labelsize=fontsize)
    axs[1].legend(map(lambda x: x[0], ps), ["Flexibility", "CO2 infra", "Power", "Conversion", "Transport"], fontsize=fontsize, frameon=True, handlelength=1.5, loc="center right")


    plt.tight_layout()
    plt.savefig("Figures/costs_subplot.pdf", dpi=1200)
    # plt.show()

    plt.close()


def main():
    ls = [# "sc_0_T_17520_cap_co2_0.0_costco2_0_ensAllowed_False_costens_3.0_pipe_and_boat.json",
      "sc_1_T_17520_cap_co2_0.0_costco2_0_ensAllowed_False_costens_3.0_only_carrier.json",
      "sc_2_T_17520_cap_co2_0.0_costco2_0_ensAllowed_True_costens_3.0_only_carrier.json",
      "sc_3_T_17520_cap_co2_None_costco2_0.08_ensAllowed_True_costens_3.0_only_carrier.json",
      "sc_4_T_17520_cap_co2_None_costco2_0.0_ensAllowed_True_costens_3.0_only_carrier.json",
      "sc_5_T_17520_cap_co2_0.0_costco2_0_ensAllowed_False_costens_3.0_only_carrier.json"
      ]

    if not os.path.exists("Figures"):
        os.makedirs("Figures")
        
    create_cost_csv(ls)
    blackout()
    energy_demand()
    price_per_scenario_cluster(ls)
    costs_subplot(ls)
    

if __name__ == '__main__':
    main()

