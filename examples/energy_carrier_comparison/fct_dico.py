#!/usr/bin/env python
# coding: utf-8

# In[ ]:


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

# NEW CASE

#filename = 'Results/sc_6_T_8760_cap_co2_0.0_costco2_0.0_ensAllowed_False_costens_3.0_pipe_and_boat.json'
# filename = 'Results/sc_1_T_8760_cap_co2_0.0_costco2_0_costens_3.0_pipe_and_boat.json'
#dico = {}
#with open(filename, "r") as fp:
    #dico = json.load(fp)
   
 #d = MakeMeReadable(dico)

# Exemple d'utilisation:

#d.solution.objective
#d.solution.elements.WIND_PLANTS_GR.variables.capacity

