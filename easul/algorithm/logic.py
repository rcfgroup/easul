from typing import List, Any
from .algorithm import Algorithm
import easul.data as ds
from .factor import Factor, FactorMatch

from .result import ScoreResult, CaseResult, Result
import logging
from attrs import define, field
from easul.expression import Case, Expression

LOG = logging.getLogger(__name__)


class Binary:
    pass


@define(kw_only=True)
class ScoreAlgorithm(Algorithm):
    """
    Score-based algorithm built from one or more factors. Also supports ranges and has a data schema.
    """
    schema: ds.DataSchema = field()
    factors:List[Factor] = field()
    ranges:List[Any] = field(factory=list)
    start_score:int = field(default=0)

    def single_result(self, data):
        dset = ds.create_input_dataset(data, self.schema, allow_multiple=False)

        matched = []

        for factor in self.factors:
            match = factor.calc_match(dset)
            if match:
                matched.append(match)

        value = self._calculate_value(matched)

        return ScoreResult(value=value, matched_factors=matched, label=self._find_label(value), ranges=self.ranges, data=dset)

    def _find_label(self, value):
        if not self.ranges:
            return None

        for rank, range in self.ranges.items():
            try:
                iter(range)

                if range[0] is None and value<=range[1]:
                    return rank

                if range[1] is None and value>=range[0]:
                    return rank

                if (range[0] is not None and value>=range[0]) and (range[1] is not None and value<=range[1]):
                    return rank
            except TypeError:
                if range == value:
                    return rank
                
        return None

    def _calculate_value(self, matched):
        value = self.start_score

        for match in matched:
            value = value + match.penalty

        return value

@define(kw_only=True)
class SelectCaseAlgorithm(Algorithm):
    """
    Algorithm based on cases, each of which are tested based on input data.
    The CaseResult returned contains the true_value from the specific case
    """
    cases:List[Case] = field()
    default_value = field(default=False)

    def single_result(self, data):
        dset = ds.create_input_dataset(data, self.schema, allow_multiple=False)

        for case in self.cases:
            if case.test(dset) is True:
                return CaseResult(value=case.true_value, matched_case=case, data=dset)

        return CaseResult(value = self.default_value, matched_case=None, data=dset)

@define(kw_only=True)
class ExpressionAlgorithm(Algorithm):
    """
    Algorithm based on an Expression which return a Result with value of 1 if true and 0 if false
    """
    expression:Expression = field()

    def single_result(self, data):
        dset = ds.create_input_dataset(data, self.schema, allow_multiple=False)
        return Result(value=1 if self.expression.evaluate(dset) else 0,data=dset)



