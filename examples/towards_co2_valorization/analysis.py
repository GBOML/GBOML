from gboml import GbomlGraph
import json
import os
import sys
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import argparse

def cost_rreh(ls:list):
    if len(ls) == 0:
        return 0.0

    cost = 0

    for ele in ls:
        # print(f"{ele = }")
        # print(dico["solution"]["elements"][ele]["objectives"])
        try:
            cost += np.sum(dico["solution"]["elements"][ele]["objectives"]["unnamed"])
        except:
            for e in dico["solution"]["elements"][ele]["objectives"]["named"].values():
                # print(f"{e = }")
                cost += e
        # print(f"{cost = }")
    
    return cost

def plot_stackplot(timehorizon, colors, labels, data):
    """
    timehorizon: N
    colors: list of colors len = M
    labels: list of labels len = M
    data: numpy array of size (M,N)
    """
    assert timehorizon == data.shape[1]
    assert data.shape[0] == len(colors) == len(labels)

    x_axis = [x for x in range(0,timehorizon)]


    plt.figure(figsize=(10,8))
    
    for c, l in zip(colors, labels):
        plt.plot([],[], color=c, label=l)


    plt.stackplot(x_axis[:timehorizon], data, colors=colors)

    plt.legend()


    plt.xlabel("Hours")
    plt.ylabel("Energy demand [GWh/h]")

    # plt.savefig("Figures/energy_demand.png", dpi=200)

class MakeMeReadable:
    def __init__(self, d):
        self.d = d
    
    def __dir__(self):
        return self.d.keys()
    
    def __getattr__(self, v):
        try:
            out = self.d[v]
            if isinstance(out, dict):
                return MakeMeReadable(out)
            return out
        except:
            return getattr(self.d, v)
        
    def __str__(self):
        return str(self.d)
    
    def __repr__(self):
        return repr(self.d)

def check_results(filename, d):
    splits = filename.split("_")
    scenario, timehorizon, cap, cost_co2, ensAllowed, cost_ens, constraint = int(splits[1]), int(splits[3]), None if splits[6] == 'None' else float(splits[6]), float(splits[8]), True if splits[10] == 'True' else False, float(splits[12]), "_".join(splits[13:])[:-5]
    # print(scenario, timehorizon, cap, cost_co2, ensAllowed, cost_ens, constraint)

    if not (d.model.horizon == timehorizon):
        print("Error file: time horizon do not match")
    
    if cap is None:
        None # TO IMPLEMENT
    else:
        if not (d.model.global_parameters.cap_co2[0] == cap):
            print("Cap not well set")
        
        try: 
            d.model.hyperedges.CAP_CO2
            # print("Cap CO2 exists")
        except:
            print("Error cap hyperedge does not exist")   
    
    if not (cost_co2 == d.model.global_parameters.co2_emission_cost[0]):
        print("Error cost CO2")
        
    if not (cost_ens == d.model.global_parameters.e_ens_cost[0]):
        print("Error cost ENS")
        
    # ["pipe_and_boat", "only_carrier", "only_pipe"]
    if constraint == "pipe_and_boat":
        try:
            d.model.nodes.PIPE_CO2
            d.model.nodes.PIPE_CO2_GR
            d.model.nodes.CARRIER_CO2
            d.model.nodes.CARRIER_CO2_GR

        except:
            print("Missing nodes", constraint)
    elif constraint == "only_carrier":
        try:
            if scenario != 5:
                d.model.nodes.CARRIER_CO2
                d.model.nodes.CARRIER_CO2_GR

        except:
            print("Missing nodes", constraint)
            print(filename)
            
    elif constraint == "only_carrier":
        try:
            d.model.nodes.PIPE_CO2
            d.model.nodes.PIPE_CO2_GR

        except:
            print("Missing nodes", constraint)
    
    if len(d.solution.elements.PIPE_CO2_CONNECTION.constraints.keys()) > 1:
        print("Error in constraints removal")

    # print("Everything else seems ok")

    return scenario, timehorizon, cap, cost_co2, ensAllowed, cost_ens, constraint


if __name__ == '__main__':
    
    ls = os.listdir("Results")
    if ".DS_Store" in ls:
        ls.remove(".DS_Store")
    ls.sort()

    with open(f'analysis.csv', "w") as fp:
        fp.write("scenario,timehorizon,cap,cost_co2,ensAllowed,cost_ens,constraint,cost_NZ,cost_GR,cost_BE,obj_cost,wind_onshore_be,wind_off_be,solar_be,ccgt_be,wind_gl,wind_sahara,solar_sahara,pccc_capa,pccc_ccgt_capa,dac_capa,dac_greenland,pipe_co2_capa,carrier_co2_capa,pipe_co2_capa_gr,carrier_co2_capa_gr\n")

    results = {}

    for f in ls:
        filename = f"Results/" + f
        print(filename)

        dico = {}
        with open(filename, "r") as fp:
            dico = json.load(fp)
            
        d = MakeMeReadable(dico)
        
        scenario, timehorizon, cap, cost_co2, ensAllowed, cost_ens, constraint = check_results(filename, d)
        results[scenario] = {"timehorizon":timehorizon, "cap":cap, "cost_co2":cost_co2, "cost_ens":cost_ens, "constraint":constraint}

        T = d.model.horizon

        folder = "Figures/" + filename[8:-5] + "/"

        if not os.path.isdir(folder):
            os.mkdir(folder)
        print(folder, os.path.isdir(folder))


        print("\nCO2 INFRACTRUCTURE")
        try:
            print("Algérie")
            if constraint in ["only_pipe", "pipe_and_boat"]:
                results[scenario]['pipe_nz'] = d.solution.elements.PIPE_CO2.variables.capacity.values[0]
                print(f"Pipe {results[scenario]['pipe_nz']:.3f}")

            if constraint in ["only_carrier", "pipe_and_boat"]:
                results[scenario]['carrier_nz'] = d.solution.elements.CARRIER_CO2.variables.capacity.values[0]
                print(f"Carrier {results[scenario]['carrier_nz']:.3f}")
        except:
            results[scenario]['carrier_nz'] = 0

        print("\n Groenland")
        if constraint in ["only_pipe", "pipe_and_boat"]:
            results[scenario]['pipe_gr'] = d.solution.elements.PIPE_CO2_GR.variables.capacity.values[0]
            print(f"Pipe {results[scenario]['pipe_gr']:.3f}")
        if constraint in ["only_carrier", "pipe_and_boat"]:
            results[scenario]['carrier_gr'] = d.solution.elements.CARRIER_CO2_GR.variables.capacity.values[0]
            print(f"Carrier {results[scenario]['carrier_gr']:.3f}\n")

        pccc_capa = dico["solution"]["elements"]["PCCC"]["variables"]["new_capacity"]["values"][0]
        pccc_ccgt_capa = dico["solution"]["elements"]["PCCC_CCGT"]["variables"]["new_capacity"]["values"][0]
        try:
            dac_capa = dico["solution"]["elements"]["DIRECT_AIR_CAPTURE_PLANTS"]["variables"]["capacity"]["values"][0]
        except:
            dac_capa = 0 # Greenland
        dac_greenland = dico["solution"]["elements"]["DIRECT_AIR_CAPTURE_PLANTS_GR"]["variables"]["capacity"]["values"][0]
        names, var = ["PCCC", "PCCC CCGT", "DAC1", "DAC2"], [pccc_capa, pccc_ccgt_capa, dac_capa, dac_greenland]

        results[scenario]["co2_capture"] = dict(zip(names, var))

        for name, v in zip(names, var):
            print(f"{name} {v:.3f}")
            
            
        plt.bar(names, var)
        plt.ylabel("ktCO2/hour")
        plt.savefig(folder + "CO2_CAPTURE_INFRACTRUCTURE.png")
        plt.close()

        print("\nCHECK BALANCE CO2")
        if constraint in ["only_pipe", "pipe_and_boat"]:
            co2_greenland = d.solution.elements.PIPE_CO2_GR.variables.flow_in.values
            try:
                co2_algeria = d.solution.elements.PIPE_CO2.variables.flow_in.values
            except:
                co2_algeria = 0
        if constraint in ["only_carrier", "pipe_and_boat"]:
            co2_greenland_carrier = d.solution.elements.CARRIER_CO2_GR.variables.flow_in.values
            try:
                co2_algeria_carrier = d.solution.elements.CARRIER_CO2.variables.flow_in.values
            except:
                co2_algeria_carrier = 0
        co2_captured_pccc = d.solution.elements.PCCC.variables.co2_captured.values
        try:
            co2_captured_dac1 = d.solution.elements.DIRECT_AIR_CAPTURE_PLANTS.variables.carbon_dioxide.values
        except:
            co2_captured_dac1 = 0

        try:
            co2_captured_dac2 = d.solution.elements.DIRECT_AIR_CAPTURE_PLANTS_GR.variables.carbon_dioxide.values
        except:
            co2_captured_dac2 = 0

        if constraint in ["only_pipe", "pipe_and_boat"]:
            plt.plot(co2_algeria, label="RREH1 pipe")
            plt.plot(co2_greenland, label="RREH2 pipe")
        if constraint in ["only_carrier", "pipe_and_boat"]:
            plt.plot(co2_algeria_carrier, label="RREH1 Boat")
            plt.plot(co2_greenland_carrier, label="RREH2 Boat")
        plt.plot(co2_captured_pccc, label="PCCC")
        plt.plot(co2_captured_dac1 , label="DAC 1")
        plt.plot(co2_captured_dac2 , label="DAC 2")
        #  plt.plot(co2_export, label="Export")
        plt.legend()

        plt.savefig(folder + "CO2_USAGE.png")
        plt.close()

        # Compare CO2 curve of emissions and capture + showing that the sum is constant
        co2_released_pccc = np.array(d.solution.elements.PCCC.variables.co2_released.values)
        co2_prod_ccgt = np.array(d.solution.elements.CCGT_BE.variables.co2_produced.values)
        co2_ccgt_captured = np.array(d.solution.elements.PCCC_CCGT.variables.co2_captured.values)
        co2_ccgt_released = np.array(d.solution.elements.PCCC_CCGT.variables.co2_released.values)
        co2_export = np.array(d.solution.elements.CO2_EXPORT.variables.exported.values)
        co2_storage_be_in = np.array(d.solution.elements.CARBON_DIOXIDE_STORAGE_BE.variables.carbon_dioxide_in.values)
        co2_storage_be_out = np.array(d.solution.elements.CARBON_DIOXIDE_STORAGE_BE.variables.carbon_dioxide_out.values)

        plt.plot(co2_captured_pccc, label="CO2 captured PCCC")
        plt.plot(co2_prod_ccgt, label="CO2 production CCGT")
        plt.plot(co2_ccgt_captured, label="CO2 Captured CCGT")
        plt.plot(co2_ccgt_released, label="CO2 Released CCGT")
        plt.plot(co2_export, label="CO2 export")
        plt.legend()
        plt.savefig(folder + "CO2_USAGE2.png")
        plt.close()

        # CO2 BALANCE
        if constraint == "pipe_and_boat":
            co2_balance = co2_captured_pccc + co2_ccgt_captured + co2_storage_be_out - co2_storage_be_in - co2_algeria - co2_greenland - co2_algeria_carrier - co2_greenland_carrier - co2_export
        elif constraint == "only_carrier":
            co2_balance = co2_captured_pccc + co2_ccgt_captured + co2_storage_be_out - co2_storage_be_in - co2_algeria_carrier - co2_greenland_carrier - co2_export
        elif constraint == "only_pipe": 
            co2_balance = co2_captured_pccc + co2_ccgt_captured + co2_storage_be_out - co2_storage_be_in - co2_algeria - co2_greenland - co2_export
        else:
            print("ERROR ERROR ERROR")
        plt.plot(co2_balance)
        plt.ylim((-0.1, 0.1))
        plt.savefig(folder + "CO2_BALANCE.png")
        plt.close()

        print(f"Total exported co2 {np.sum(co2_export):.3f}")
        print(f"Total CO2 released in atm: {np.sum(co2_ccgt_released + co2_released_pccc):.3f}")
        co2_balance_atm = co2_ccgt_released + co2_released_pccc - co2_captured_dac1 - co2_captured_dac2
        print("Is the system 0 net emission? ", np.sum(co2_balance_atm) < 0.0000001)
        print(f"Balance of CO2 in the atm {np.sum(co2_balance_atm):.3f}")


        print("\nCheck Power Generation")
        print("New capacity Installed")
        wind_onshore_be = d.solution.elements.WIND_ONSHORE_BE.variables.new_capacity.values[0]
        wind_off_be = d.solution.elements.WIND_OFFSHORE_BE.variables.new_capacity.values[0]
        solar_be = d.solution.elements.SOLAR_BE.variables.new_capacity.values[0]
        # nuke_be = d.solution.elements.NUCLEAR.variables.new_capacity.values[0]
        ccgt_be = d.solution.elements.CCGT_BE.variables.new_capacity.values[0]
        try:
            wind_gl = d.solution.elements.WIND_PLANTS_GR.variables.capacity.values[0]
        except:
            wind_gl = 0

        try:
            wind_sahara = d.solution.elements.WIND_PLANTS.variables.capacity.values[0]
            solar_sahara = d.solution.elements.SOLAR_PV_PLANTS.variables.capacity.values[0]
        except:
            wind_sahara = 0
            solar_sahara = 0


        names = ["wind on",
                 "wind off",
                "solar_be",
                "ccgt_be",
                "wind_gl",
                "wind_nz",
                "solar_nz"]
        var = [wind_onshore_be,
               wind_off_be,
                solar_be,
                ccgt_be,
                wind_gl,
                wind_sahara,
                solar_sahara]

        results[scenario]["new_power_capacity"] = dict(zip(names, var))
                 
        for name, v in zip(names, var):
            print(f"{name} {v:.3f}")
                 
        plt.bar(names, var)
        plt.ylabel("GW")
        plt.savefig(folder + "NEW_POWER_GENERATION.png")
        plt.close()


        print("\nTotal capacity installed")
        wind_onshore_be = d.solution.elements.WIND_ONSHORE_BE.variables.new_capacity.values[0] + d.model.nodes.WIND_ONSHORE_BE.parameters.pre_installed_capacity[0]
        wind_off_be = d.solution.elements.WIND_OFFSHORE_BE.variables.new_capacity.values[0] + d.model.nodes.WIND_OFFSHORE_BE.parameters.pre_installed_capacity[0]

        solar_be = d.solution.elements.SOLAR_BE.variables.new_capacity.values[0] + d.model.nodes.SOLAR_BE.parameters.pre_installed_capacity[0]
        # nuke_be = d.solution.elements.NUCLEAR.variables.new_capacity.values[0] + d.model.nodes.NUCLEAR.parameters.pre_installed_capacity[0]
        ccgt_be = d.solution.elements.CCGT_BE.variables.new_capacity.values[0] + d.model.nodes.CCGT_BE.parameters.pre_installed_capacity[0]
        try:
            wind_gl = d.solution.elements.WIND_PLANTS_GR.variables.capacity.values[0]
        except:
            wind_gl = 0

        try:
            wind_sahara = d.solution.elements.WIND_PLANTS.variables.capacity.values[0]
            solar_sahara = d.solution.elements.SOLAR_PV_PLANTS.variables.capacity.values[0]
        except:
            wind_sahara = 0
            solar_sahara = 0

        names = ["wind on",
                 "wind off",
                "solar_be",
                "ccgt_be",
                "wind_gl",
                "wind_nz",
                "solar_nz"]
        var = [wind_onshore_be,
               wind_off_be,
                solar_be,
                ccgt_be,
                wind_gl,
                wind_sahara,
                solar_sahara]

        results[scenario]["total_power_capacity"] = dict(zip(names, var))
                 
        for name, v in zip(names, var):
            print(f"{name} {v:.3f}")
                 
        plt.bar(names, var)
        plt.ylabel("GW")
        plt.savefig(folder + "POWER_GENERATION.png")
        plt.close()

        print("\nLATEX FORMAT")
        print("\\hline")
        print("Technology & Capacity (GW) \\\\")
        print("\\hline")
        for name, v in zip(names, var):
            print(f"{name} & {v:.2f} \\\\")
            
        print("\\hline")

        elec_demand = np.array(d.model.global_parameters.demand_el[:T])
        elec_demand_pccc = np.array(d.solution.elements.PCCC.variables.e_consumed.values)
        elec_demand_pccc_ccgt = np.array(d.solution.elements.PCCC_CCGT.variables.e_consumed.values)
        elec_demand_co2_storage = np.array(d.solution.elements.CARBON_DIOXIDE_STORAGE_BE.variables.electricity.values)
        if constraint in ["only_pipe", "pipe_and_boat"]:
            elec_demand_pipe_nz = np.array(d.solution.elements.PIPE_CO2.variables.e_consumed.values)
            elec_demand_pipe_gr = np.array(d.solution.elements.PIPE_CO2_GR.variables.e_consumed.values)
            elec_demand_tot = np.array(elec_demand) + elec_demand_pccc + elec_demand_pccc_ccgt + elec_demand_co2_storage + elec_demand_pipe_nz + elec_demand_pipe_gr
        else:
            elec_demand_tot = np.array(elec_demand) + elec_demand_pccc + elec_demand_pccc_ccgt + elec_demand_co2_storage
        ens = d.solution.elements.ENERGY_DEMAND_BE.variables.e_ens.values
        elec_served = elec_demand_tot - ens

        plt.plot(ens, label="ens")
        plt.plot(elec_demand, label="elec_demand")
        plt.plot(elec_demand_tot, label="elec_demand_tot")
        plt.plot(elec_served, label="Elec Served")
        plt.ylim((0,24))
        plt.legend()
        plt.savefig(folder + "ELEC_DEMAND.png")
        plt.close()

        elec_prod_ccgt_be = np.array(d.solution.elements.CCGT_BE.variables.e_produced.values)
        elec_prod_wind_off_be = np.array(d.solution.elements.WIND_OFFSHORE_BE.variables.e_produced.values)
        elec_prod_wind_on_be = np.array(d.solution.elements.WIND_ONSHORE_BE.variables.e_produced.values)
        elec_prod_solar_be = np.array(d.solution.elements.SOLAR_BE.variables.e_produced.values)

        elec_prod_tot = elec_prod_ccgt_be + elec_prod_wind_off_be + elec_prod_wind_on_be + elec_prod_solar_be

        colors = ["blue", "red", "orange", "green"]
        labels = ['elec_prod_ccgt_be','elec_prod_wind_off_be','elec_prod_wind_on_be', 'elec_prod_solar_be']
        data = np.stack([elec_prod_ccgt_be, elec_prod_wind_off_be, elec_prod_wind_on_be, elec_prod_solar_be])
        print(data.shape)
        plot_stackplot(T, colors, labels, data)
        plt.savefig(folder + "ELEC_PROD_STACK.png")
        plt.close()

        if constraint in ["only_pipe", "pipe_and_boat"]:
            colors = ["green", "orange", "blue", "red", "yellow", "purple"]
            labels = ['PCCC CCGT','PCCC','co2 storage', 'pipe nz', 'pipe gr', 'Elec Demand']
            data = np.stack([elec_demand_pccc_ccgt, elec_demand_pccc, elec_demand_co2_storage, elec_demand_pipe_nz, elec_demand_pipe_gr, elec_demand])
        else:
            colors = ["green", "orange", "blue", "purple"]
            labels = ['PCCC CCGT','PCCC','co2 storage', 'Elec Demand']
            data = np.stack([elec_demand_pccc_ccgt, elec_demand_pccc, elec_demand_co2_storage, elec_demand])
        kwargs= {
                 "xlabel": "Hours",
                 "ylabel": "Energy demand [GWh/h]",
                }
        plot_stackplot(T, colors, labels, data)
        plt.savefig(folder + "ELEC_DEMAND_STACK.png")
        plt.close()

        ##########################################################
        ######################## GAS #############################
        ##########################################################

        print("\nCheck Gas balance")
        gas = np.array(d.solution.elements.LIQUEFIED_METHANE_REGASIFICATION.variables.methane.values) * 15.31
        # gas_rreh2 = d.solution.elements.LIQUEFIED_METHANE_REGASIFICATION_GR.variables.methane.values

        gas_cons_ccgt = d.solution.elements.CCGT_BE.variables.ng_consumed.values[:T]
        gas_demand = d.model.hyperedges.DESTINATION_METHANE_BALANCE.parameters.demand[:T]

        plt.plot(gas, label="gas import")
        # plt.plot(gas_rreh2, label="gas_rreh2")

        plt.plot(gas_cons_ccgt, label="gas_cons_ccgt")
        plt.plot(gas_demand, label="gas_demand")


        plus = np.array(gas_cons_ccgt) + np.array(gas_demand) 
        # plt.plot(plus, label="gas_cons_ccgt + gas_demand")
        plt.ylim((0,50))

        plt.legend()
        plt.savefig(folder + "GAS_IMPORT_EXPORT.png")
        plt.close()

        balance = gas - (plus)
        plt.plot(balance)
        plt.ylim((-0.1, 0.1))
        plt.savefig(folder + "GAS_BALANCE.png")
        plt.close()


        try:
            liquid_gas = np.array(d.solution.elements.METHANE_LIQUEFACTION_PLANTS.variables.liquefied_methane.values)
            storage_out_liquid_gas = np.array(d.solution.elements.LIQUEFIED_METHANE_STORAGE_HUB.variables.liquefied_methane_out.values)
            storage_in_liquid_gas = np.array(d.solution.elements.LIQUEFIED_METHANE_STORAGE_HUB.variables.liquefied_methane_in.values)
            carrier_in_liquid_gas = np.array(d.solution.elements.LIQUEFIED_METHANE_CARRIERS.variables.liquefied_methane_in.values)
            methane_carrier_co2 = np.array(d.solution.elements.CARRIER_CO2.variables.methane_in.values) * 15.3

            plt.plot(liquid_gas, label="liquid_gas")
            plt.plot(storage_out_liquid_gas, label="storage_out_liquid_gas")
            plt.plot(storage_in_liquid_gas, label="storage_in_liquid_gas")
            plt.plot(carrier_in_liquid_gas, label="carrier_in_liquid_gas")
            plt.plot(methane_carrier_co2, label="methane_carrier_co2")
            plt.savefig(folder + "GAS_LIQUID_USAGE_NZ.png")
            plt.close()

            balance = liquid_gas + storage_out_liquid_gas - storage_in_liquid_gas - carrier_in_liquid_gas - methane_carrier_co2

            plt.plot(balance)
            plt.ylim((-0.01, 0.01))
            plt.savefig(folder + "GAS_LIQUEFIED_BALANCE_NZ.png")
            plt.close()
        except:
            plt.close()

        try:
            liquid_gas = np.array(d.solution.elements.METHANE_LIQUEFACTION_PLANTS_GR.variables.liquefied_methane.values)
            storage_out_liquid_gas = np.array(d.solution.elements.LIQUEFIED_METHANE_STORAGE_HUB_GR.variables.liquefied_methane_out.values)
            storage_in_liquid_gas = np.array(d.solution.elements.LIQUEFIED_METHANE_STORAGE_HUB_GR.variables.liquefied_methane_in.values)
            carrier_in_liquid_gas = np.array(d.solution.elements.LIQUEFIED_METHANE_CARRIERS_GR.variables.liquefied_methane_in.values)
            methane_carrier_co2 = np.array(d.solution.elements.CARRIER_CO2_GR.variables.methane_in.values) * 15.3

            plt.plot(liquid_gas, label="liquid_gas")
            plt.plot(storage_out_liquid_gas, label="storage_out_liquid_gas")
            plt.plot(storage_in_liquid_gas, label="storage_in_liquid_gas")
            plt.plot(carrier_in_liquid_gas, label="carrier_in_liquid_gas")
            plt.savefig(folder + "GAS_LIQUIEFIED_USAGE_GR.png")
            plt.close()

            balance = liquid_gas + storage_out_liquid_gas - storage_in_liquid_gas - carrier_in_liquid_gas - methane_carrier_co2

            plt.plot(balance)
            plt.ylim((-0.01, 0.01))
            plt.savefig(folder + "GAS_LIQUEFIED_BALANCE_GR.png")
            plt.close()
        except:
            plt.close()

        # FLUX OUT
        try:
            methane_rreh1 = d.solution.elements.LIQUEFIED_METHANE_CARRIERS.variables.liquefied_methane_out.values
            methane_rreh2 = d.solution.elements.LIQUEFIED_METHANE_CARRIERS_GR.variables.liquefied_methane_out.values
        except:
            methane_rreh1 = 0
            methane_rreh2 = 0
        
        methane_storage_out_BE = d.solution.elements.LIQUEFIED_METHANE_STORAGE_DESTINATION.variables.liquefied_methane_out.values

        # FLUX IN
        methane_storage_in_BE = d.solution.elements.LIQUEFIED_METHANE_STORAGE_DESTINATION.variables.liquefied_methane_in.values
        methane_to_regas = d.solution.elements.LIQUEFIED_METHANE_REGASIFICATION.variables.liquefied_methane.values

        plt.plot(methane_rreh1, label="methane_rreh1")
        plt.plot(methane_rreh2, label="methane_rreh2")

        plt.plot(methane_storage_out_BE, label="methane_storage_out_BE")
        plt.plot(methane_to_regas, label="methane_to_regas")

        plt.legend()
        plt.savefig(folder + "GAS_LIQUID.png")
        plt.close()

        balance = np.array(methane_rreh1) + np.array(methane_rreh2) + np.array(methane_storage_out_BE) - np.array(methane_storage_in_BE) - np.array(methane_to_regas)
        plt.plot(balance)
        plt.ylim((-0.01, 0.01))
        plt.savefig(folder + "GAS_LIQUID_BALANCE.png")
        plt.close()

        print("Check ")

        try:
            pipe_co2_capa = d.solution.elements.PIPE_CO2.variables.capacity.values[0]
        except:
            pipe_co2_capa = 0
        try:
            carrier_co2_capa = d.solution.elements.CARRIER_CO2.variables.capacity.values[0]
        except:
            carrier_co2_capa = 0
        try:
            pipe_co2_capa_gr = d.solution.elements.PIPE_CO2_GR.variables.capacity.values[0]
        except:
            pipe_co2_capa_gr = 0
        try:
            carrier_co2_capa_gr = d.solution.elements.CARRIER_CO2_GR.variables.capacity.values[0]
        except:
            carrier_co2_capa_gr = 0

        names, var = ["pipe_co2", "carrier_co2", "pipe_co2_gr", "carrier_co2_gr"], [pipe_co2_capa, carrier_co2_capa, pipe_co2_capa_gr, carrier_co2_capa_gr]
        plt.bar(names, var)
        plt.ylabel("ktCO2/hour")
        plt.savefig(folder + "CO2_TRANSPORT_INFRACTRUCTURE.png")
        plt.close()

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

        cost_NZ = cost_rreh(NZ_nodes)
        cost_GR = cost_rreh(GR_nodes)
        cost_BE = cost_rreh(BE_nodes)


        print(f"NZ {cost_NZ = }")
        print(f"GR {cost_GR = }")
        print(f"BE {cost_BE = }")


        obj_cost = d.solution.objective
        tot_cost = np.sum([cost_NZ, cost_GR, cost_BE])

        abs_diff = np.abs(d.solution.objective - np.sum([cost_NZ, cost_GR, cost_BE]))
        print(f"{obj_cost = }")
        print(f"{tot_cost = }")
        print(abs_diff < 0.1)
        print()

        gas = np.array(d.solution.elements.LIQUEFIED_METHANE_REGASIFICATION.variables.methane.values) * 15.31 # kt/h * GWh/kt
        gas_prod = np.sum(gas) # GWh
        cost_to_remove = cost_rreh(["CCGT_BE", "CO2_EXPORT","ENERGY_DEMAND_BE",
                            "WIND_ONSHORE_BE","WIND_OFFSHORE_BE","SOLAR_BE",])
        cost_per_kwh = (obj_cost - cost_to_remove) / gas_prod # M€ / GWh = €/kwh 
        print(f"{cost_per_kwh = :.4f}")
        print()

        results[scenario]["ch4_cost_per_kwh"] = cost_per_kwh

        print(f"{scenario},{timehorizon},{cap},{cost_co2},{ensAllowed},{cost_ens},{constraint},{cost_NZ},{cost_GR},{cost_BE},{obj_cost},{wind_onshore_be},{wind_off_be},{solar_be},{ccgt_be},{wind_gl},{wind_sahara},{solar_sahara},{pccc_capa},{pccc_ccgt_capa},{dac_capa},{dac_greenland},{pipe_co2_capa},{carrier_co2_capa},{pipe_co2_capa_gr},{carrier_co2_capa_gr}\n")
        with open(f'analysis.csv', "a") as fp:
            fp.write(f"{scenario},{timehorizon},{cap},{cost_co2},{ensAllowed},{cost_ens},{constraint},{cost_NZ},{cost_GR},{cost_BE},{obj_cost},{wind_onshore_be},{wind_off_be},{solar_be},{ccgt_be},{wind_gl},{wind_sahara},{solar_sahara},{pccc_capa},{pccc_ccgt_capa},{dac_capa},{dac_greenland},{pipe_co2_capa},{carrier_co2_capa},{pipe_co2_capa_gr},{carrier_co2_capa_gr}\n")

    # LATEX FORMAT OF THE PARAMETERS 
    for f in ls:
        filename = f"Results/" + f

        dico = {}
        with open(filename, "r") as fp:
            dico = json.load(fp)
            
        d = MakeMeReadable(dico)

        scenario, timehorizon, cap, cost_co2, ensAllowed, cost_ens, constraint = check_results(filename, d)

        if ensAllowed:
            print(f"{scenario} & {timehorizon} & {cap} & {cost_co2} & {ensAllowed} & {cost_ens} & {constraint.replace('_', ' ')} & {d.solution.objective:.2f} \\\\")
        else:
            print(f"{scenario} & {timehorizon} & {cap} & {cost_co2} & {ensAllowed} & - & {constraint.replace('_', ' ')} & {d.solution.objective:.2f} \\\\")

    with open(f'analysis.json', "w") as fp:
        json.dump(results, fp, indent=4)





