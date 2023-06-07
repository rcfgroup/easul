import operator
import re
from abc import abstractmethod
from typing import Callable

from attrs import define, field
import numpy as np
import pandas as pd
from easul.error import MissingValue
import logging
LOG = logging.getLogger(__name__)

@define(kw_only=True)
class Expression:
    """
    Base Expression class. Derived classes evaluate input data and return a True/False
    """
    label = ""
    empty_values = [None, np.nan]

    @abstractmethod
    def evaluate(self, data):
        pass

    @classmethod
    def is_empty(cls, item):
        if item in cls.empty_values:
            return True

        try:
            if np.isnan(item):
                return True
        except TypeError:
            pass

        return False

@define(kw_only=True)
class FieldExpression(Expression):
    """
    Expression which tests a specific input field.
    """
    input_field: str = field()
    ignore_empty: bool = field(default=False)

    def evaluate(self, data):
        try:
            item = data[self.input_field]
        except TypeError:
            item = data.value

        if self.is_empty(item):
            if self.ignore_empty is True:
                return False

            raise MissingValue(f"Data item '{self.input_field}' is empty and cannot be ignored")

        return self._test(item)



@define(kw_only=True)
class OperatorExpression(FieldExpression):
    """
    Expression which utilises a function (e.g. from Python operators) to perform its test on a particular field.
    The operator function is passed the field value and a defined value to compare it against.
    """
    operator: Callable = field()
    value: int = field()

    def _test(self, item):
        return bool(self.operator(item,self.value))

    @property
    def label(self):
        docstring = str(self.operator.__doc__)
        docstring = docstring.replace("Same as ", "")

        label = docstring.replace("a","[a]").replace("b","[b]")
        label = label.replace("[a]", self.input_field).replace("[b]", str(self.value)).replace(".","")
        return label

@define(kw_only=True)
class NullExpression(FieldExpression):
    """
    Expression which determines if a field value is None.
    If it does not exist in the input data then it is replaced by a defined 'value' and tested against this.
    """
    def evaluate(self, data):
        try:
            item = data[self.input_field]
        except TypeError:
            item = data.value

        return item is None

    @property
    def label(self):
        return self.input_field + " is null"


@define(kw_only=True)
class EmptyExpression(FieldExpression):
    """
    Expression which determines if a field value is empty or full (if negated = True).
    """
    negated = field(default=False)

    def evaluate(self, data):
        if self.negated:
            return not self.is_empty(data[self.input_field])
        else:
            return self.is_empty(data[self.input_field])

    @property
    def label(self):
        return self.input_field + " is " + "not" if self.negated else "" + " empty"




@define(kw_only=True)
class MultiExpression:
    """
    Base class for an expression which tests multiple expressions according to a multi-logic function (e.g. or)
    """
    expressions = field()
    title:str = field(default=None)
    logic = None
    join_label = ""

    def evaluate(self, data):
        return bool(self.logic(*[c.evaluate(data) for c in self.expressions]))

    @property
    def label(self):
        return (" " + self.join_label + " ").join([c.label for c in self.expressions])

@define(kw_only=True)
class BetweenExpression(FieldExpression):
    """
    Expression which determines if a field value is between (e.g. greater or equal to OR less or equal to) defined
    from and to values.
    """
    from_value = field()
    to_value = field()

    def _test(self, item):
        return bool(item>=self.from_value and item<=self.to_value)

    @property
    def label(self):
        return f"{self.input_field} between {self.from_value} and {self.to_value}"

@define(kw_only=True)
class OrExpression(MultiExpression):
    """
    Expression which tests whether one expression OR another is true
    """
    logic = operator.or_
    join_label = "or"


@define(kw_only=True)
class RegexExpression(FieldExpression):
    """
    Expression which checks whether a field value matches/does not match a regular expression pattern
    """
    input_field = field()
    pattern = field()
    negated = field(default=False)

    def _test(self, item):
        if not item or pd.isna(item):
            return self.negated

        match = re.search(self.pattern, item)

        if self.negated:
            return False if match else True
        else:
            return True if match else False

    def label(self):
        return f"{self.input_field} matches {self.pattern}"

@define(kw_only=True)
class QueryCountExpression(Expression):
    """
    Expression which uses an operator function to test how many rows (value) in a pandas DataFrame meet a specific
    query.
    """
    query = field()
    operator = field()
    value = field()
    label = field()

    def evaluate(self, dset):

        queried_data = dset.data.query(self.query)
        rows = queried_data.shape[0]

        if self.operator(rows, self.value):
            return True

        return False


@define(kw_only=True)
class Case:
    """
    Simple Case class which includes an expression, the value returned if True and a title for documentation/help.
    """
    expression = field()
    true_value = field(default=True)
    title = field(default=None)

    def asdict(self):
        return {
            "expression":str(self.expression),
            "true_value":str(self.true_value)
        }

    def test(self, dset):
        return self.expression.evaluate(dset)

@define(kw_only=True)
class DecisionCase:
    """
    Case class used by Decision classes which instead of a value if true returns a Step.
    """
    expression = field()
    true_step = field(default=None)
    title = field(default=None)

    def asdict(self):
        return {
            "expression":str(self.expression),
            "true_step":str(self.true_step.name if self.true_step else "")
        }

    def test(self, dset):
        return self.expression.evaluate(dset)