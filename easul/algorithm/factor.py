from typing import Optional, Any, Callable

from attrs import define, field
from abc import abstractmethod

from easul.error import MissingValue
from easul.expression import OperatorExpression, Expression


@define(kw_only=True)
class Factor:
    """
    Base factor for score-based algorithm
    """
    title:str = field(default=None)
    ignore_empty:bool = field(default=False)

    @abstractmethod
    def calc_match(self, dset):
        pass

@define(kw_only=True)
class ExpressionFactor:
    """
    Factor based on a variable expression which if true uses the defined penalty.
    """
    expression:Expression = field()
    penalty: float = field()
    title:str = field()
    ignore_empty:bool = field(default=False)

    def calc_match(self, dset):
        if self.expression.evaluate(dset) is True:
            return FactorMatch(factor = self, matched_data=dset, penalty=self.penalty)
        else:
            return None

@define(kw_only=True)
class PenaltyValueFactor(Factor):
    """
    Factor which uses the value of any input field as the penalty.
    """
    input_field:str = field()
    title:str = field()
    ignore_empty:bool = field(default=False)
    empty_value:Optional[Any] = field(default=0)

    def calc_match(self, dset):
        penalty = dset.get(self.input_field)
        if Expression.is_empty(penalty):
            if self.ignore_empty:
                return EmptyFactorMatch(factor=self, matched_data=dset, penalty=self.empty_value)

            raise MissingValue(f"Data item '{self.input_field}' in factor is empty and cannot be ignored")

        return FactorMatch(factor=self, matched_data=dset, penalty=penalty)


@define(kw_only=True)
class OperatorFactor(ExpressionFactor):
    """
    Expression factor which utilises an operator function (e.g. from Python operators) which if true uses the defined
    penalty.
    """
    operator:Callable = field()
    input_field:str = field()
    value:Optional[Any] = field()
    ignore_empty: bool = field(default=False)
    expression = field(init=False)

    @expression.default
    def _default_expression(self):
        return OperatorExpression(operator = self.operator, value = self.value, input_field=self.input_field, ignore_empty = self.ignore_empty)


@define(kw_only=True)
class FactorMatch:
    """
    Matched factor for score.
    """
    factor:"easul.algorithm.ScoreFactor" = field()
    matched_data:Any = field()
    penalty: float = field()

    def asdict(self):
        if hasattr(self.factor,"expression"):
            expression = self.factor.expression.label
        else:
            expression = "?"

        return {
            "title":self.factor.title,
            "penalty":self.penalty,
            "expression":expression,
            "empty":False
        }


@define(kw_only=True)
class EmptyFactorMatch:
    """
    Empty factor match for score which is used when 'ignore_empty' flag is set in Factor and no value is supplied
    in the field.
    """
    factor:"easul.algorithm.ScoreFactor" = field()
    matched_data = field()
    penalty = field()

    def asdict(self):
        if hasattr(self.factor,"expression"):
            expression = self.expression.label
        else:
            expression = "?"

        return {
            "title":self.factor.title,
            "penalty":self.penalty,
            "expression":expression,
            "empty":True
        }