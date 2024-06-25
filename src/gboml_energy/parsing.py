import pathlib
from dataclasses import dataclass

from lark import v_args

from gboml.ast import ExpressionObj, Function
from gboml.parsing import GBOMLParser, default_lark_def, _vargs

# adds new rules to the std defs
energy_lark_def = default_lark_def + "\n" + open((pathlib.Path(__file__).parent / "gboml_energy.lark").resolve()).read()

@dataclass
class UnitExpression(ExpressionObj):
    """ An Expression with a Unit """
    value: int | float | Function
    unit: dict[str, int]


power_of_ten = {"p": -12, "n": -9, "mu": -6, "m": -3, "k": 3, "M": 6, "G": 9, "T": 12}


class GBOMLEnergyParser(GBOMLParser):
    def __init__(self):
        super().__init__(energy_lark_def)

    @v_args(wrapper=_vargs)
    class GBOMLLarkTransformer(GBOMLParser.GBOMLLarkTransformer):
        def UNIT(self, token):
            content = token.value.split("_")
            if len(content) == 1 and token.value.endswith("_") and content[0] in power_of_ten:
                return {"10": power_of_ten[content[0]]}
            if len(content) > 1 and content[0] in power_of_ten:
                return {"10": power_of_ten[content[0]]} | {x: 1 for x in content[1:]}
            return {x: 1 for x in content}

        def value(self, meta, value, unit=None):
            if unit is not None:
                return UnitExpression(value, unit, meta=meta)
            return value

        def _merge_with_factors(self, content, factor):
            out = content[0]
            for other in content[1:]:
                for entry, v in other.items():
                    out[entry] = out.get(entry, 0) + v * factor
                    if out[entry] == 0:
                        del out[entry]
            return out

        def mul_unit_expr(self, meta, *content):
            return self._merge_with_factors(content, 1)

        def div_unit_expr(self, meta, *content):
            return self._merge_with_factors(content, -1)

        def exp_unit_expr(self, meta, *content):
            return {x: y * content[1] for x, y in content[0].items()}

content = """
#TIMEHORIZON
    T = 8760;
#GLOBAL
    a = 2 |MWh|;
    b = 2 |€| * 4 |Wc|;
    c = 2 |€ * k_Wc / h * V * Wc * k_€ * k_T ** 2|;
#NODE A
    prix = 0.01 |€/MWh|;
    
    #VARIABLES
        pass;
    //internal: c[T] |MWh|;
    //internal: p[T] |€|;
    
    #CONSTRAINTS
    c[t] * prix == p[t];
"""

print(GBOMLEnergyParser().parse(content))
