import ast
import typing
from dataclasses import dataclass, field
from enum import Enum
from functools import reduce
from gboml.ast.base import to_python_ast, to_balanced_python_ast, GBOMLObject
from gboml.ast.expressions import ExpressionObj, BoolExpressionObj

if typing.TYPE_CHECKING:
    from gboml.ast.values import Expression, PossiblyGeneratedExpression

@dataclass(frozen=True)
class _Operator:
    symbol: str
    is_left_associative: typing.Optional[bool] = field(repr=False)
    ast_fun: typing.Callable[[], ast.operator] = field(repr=False)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.symbol == other
        return NotImplemented  # and shouldn't be implemented

    def __repr__(self): return self.symbol

    def __hash__(self): return hash(self.symbol)


class Operator(Enum):  # can be instanced with `Operator("<")`
    lesser          = _Operator("<", True, ast.Lt)
    greater         = _Operator(">", True, ast.Gt)
    lesser_or_equal = _Operator("<=", True, ast.LtE)
    greater_or_equal= _Operator(">=", True, ast.LtE)
    equal           = _Operator("==", True, ast.Eq)
    not_equal       = _Operator("!=", True, ast.NotEq)
    concatenation   = _Operator("|", True, None)  # TODO
    times           = _Operator("*", None, ast.Mult)
    divide          = _Operator("/", True, ast.Div)
    plus            = _Operator("+", None, ast.Add)
    minus           = _Operator("-", True, ast.Sub)
    exponent        = _Operator("**", False, ast.Pow)
    unary_minus     = _Operator("u-", None, ast.USub)
    modulo          = _Operator("%", True, ast.Mod)
    b_and           = _Operator("and", True, ast.And)  # True because short-circuit e.g. `len(a) != 0 && a[0] != 0`
    b_or            = _Operator("or", True, ast.Or)
    b_not           = _Operator("not", None, ast.Not)


@dataclass(frozen=True)
class ExpressionOp(ExpressionObj):
    operator: Operator
    operands: tuple["Expression"]
    
    def _to_python_ast(self, scope: 'Scope'):
        if self.operator is Operator.unary_minus:
            # if operand is a value, return a negative Constant (evaluated 2x faster than UnaryOp(USub, Constant))
            return ast.UnaryOp(op=ast.USub(), operand=to_python_ast(self.operands[0], scope)) if isinstance(self.operands[0], GBOMLObject) else ast.Constant(-self.operands[0])
        else:
            to_ast_with_scope = lambda operand: to_python_ast(operand, scope)
            match self.operator.value.is_left_associative:
                case True: return reduce(lambda l,r: ast.BinOp(left=l, op=self.operator.value.ast_fun(), right=r), map(to_ast_with_scope, self.operands))
                case False: return reduce(lambda r,l: ast.BinOp(left=l, op=self.operator.value.ast_fun(), right=r), map(to_ast_with_scope, reversed(self.operands)))
                case None: return to_balanced_python_ast(self.operands, lambda l,r: ast.BinOp(left=l, op=self.operator.value.ast_fun(), right=r), scope)


@dataclass(frozen=True)
class BoolExpressionOp(BoolExpressionObj):
    operator: Operator
    operands: tuple["Expression"]


@dataclass(frozen=True)
class BoolExpressionComparison(BoolExpressionObj):
    lhs: "Expression"
    operator: Operator
    rhs: "Expression"

    def __bool__(self):
        """ Checks if lhs and rhs are *exactly* the same tree in an eq relation """
        #TODO improve me
        if self.operator == Operator.equal:
            return self.lhs is self.rhs
        return False


@dataclass(frozen=True)
class ExpressionFunctionCall(ExpressionObj):
    lhs: "Expression"
    operands: tuple["PossiblyGeneratedExpression"]


@dataclass(frozen=True)
class ExpressionDotCall(ExpressionObj):
    lhs: "Expression"
    rhs: str


@dataclass(frozen=True)
class ExpressionArrayCall(ExpressionObj):
    lhs: "Expression"
    rhs: "Expression"
