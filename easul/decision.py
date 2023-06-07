from abc import abstractmethod

from attrs import define, field

from easul.algorithm import Result
from easul.outcome import Outcome, ResultOutcome
from easul.expression import DecisionCase

@define(kw_only=True)
class Decision:
    """
    Decides the outcome based on the provided result and the type of decision. The outcome includes the next step,
    the result and other contextual information.
    """
    @abstractmethod
    def decide_outcome(self, result, context, data, step):
        pass

    @property
    def possible_links(self):
        return {}

    def describe(self):
        return {
            "type":self.__class__.__name__
        }

import logging
LOG = logging.getLogger(__name__)

def get_result_value(result, field):
    """
    Extract value from result object or result dictionary.
    Args:
        result:
        field:

    Returns:

    """
    if issubclass(result.__class__, Result):
        return getattr(result, field)

    return result[field]

@define(kw_only=True)
class BinaryDecision(Decision):
    """
    Binary decision which returns a true/false outcome based on the algorithm result being the defined positive value.
    """
    true_step = field()
    false_step = field()
    input_field = field(default="value")
    positive_value = field(default=1)
    positive_label = field(default="positive")
    negative_label = field(default="negative")

    def describe(self):
        desc = super().describe()
        desc.update({
            "true_step":self.true_step.title + "(" + self.true_step.name + ")",
            "false_step":self.false_step.title + "(" + self.false_step.name + ")",
            "input_field":self.input_field,
            "positive_value":self.positive_value,
            "positive_label":self.positive_label,
            "negative_label":self.negative_label
        })
        return desc

    def decide_outcome(self, result, context, data, step):
        positive_outcome = 1 if get_result_value(result, self.input_field) == self.positive_value else 0

        return ResultOutcome(
            outcome_step=step,
            next_step=self.true_step if positive_outcome == 1 else self.false_step,
            value=positive_outcome,
            result=result,
            context=context,
            input_data=data,
            reason="positive" if positive_outcome == 1 else "negative"
        )

    @property
    def possible_links(self):
        return {self.positive_label:self.true_step, self.negative_label:self.false_step}

@define(kw_only=True)
class PassThruDecision(Decision):
    """

    """
    next_step = field()

    def describe(self):
        desc = super().describe()
        desc.update({
            "next_step": self.next_step.title + "(" + self.next_step.name + ")",
        })
        return desc

    def decide_outcome(self, result, context, data, step):
        return ResultOutcome(
            outcome_step=step,
            next_step=self.next_step,
            value=result.value,
            result=result,
            context=context,
            input_data=data,
            reason="next"
        )

    @property
    def possible_links(self):
        return {"next":self.next_step}


@define(kw_only=True)
class StepResultDecision(Decision):
    """
    Decision which returns the outcome and next step based on the value of the algorithm result.
    """
    step_field = field()

    def describe(self):
        desc = super().describe()
        desc.update({
            "step_field": self.step_field
        })
        return desc


    def decide_outcome(self, result, context, data, step):
        return Outcome(
            outcome_step=step,
            next_step=result[self.step_field],
            reason=""
        )

@define(kw_only=True)
class SelectCaseDecision(Decision):
    """
    Decision which returns an outcome and next step based on a set of cases (StepCase objects).
    """
    cases = field()
    default_step = field(default=None)

    def describe(self):
        desc = super().describe()
        desc.update({
            "cases": [c.title for c in self.cases]
        })
        if self.default_step:
            desc["default_step"] = self.default_step.title + "(" + self.default_step.name + ")"

        return desc

    def decide_outcome(self, result, context, data, step):
        for case in self.cases:
            if case.expression.evaluate(result):
                return ResultOutcome(outcome_step=step, next_step=case.true_step, reason=case.expression.label,
                                      input_data=data, context=context, result=result, value=None)

        return ResultOutcome(outcome_step=step, next_step=self.default_step, reason="default",
                                  input_data=data, context=context, result=result, value=None)

    @property
    def possible_links(self):
        links = {case.title if case.title else case.expression.label: case.true_step for case in self.cases}
        if self.default_step:
            links["default"]=self.default_step

        return links

@define(kw_only=True)
class RankedDecision(SelectCaseDecision):
    """
    Extension of SelectCaseDecision which includes focuses on checking ranks which are turned into cases (e.g. low, medium, high) and operators.
    """
    ranks = field()
    input_field = field()
    cases = field(init=False)

    def __attrs_post_init__(self):
        from easul.expression import OperatorExpression
        import operator
        self.cases = [
            DecisionCase(expression=OperatorExpression(input_field=self.input_field, value=value, operator=operator.eq),
                         true_step=rank_step) for value, rank_step in self.ranks.items()]

@define(kw_only=True)
class CompareInputAndResultDecision(Decision):
    """
    Decision which returns one next step (true_step) if the value from input is the same as the result of the algorithm and
    another next step (false_step) is not.
    """
    input_field = field()
    true_step = field()
    false_step = field()
    input_mapping = field(default=None)
    result_mapping = field(default=None)
    
    def decide_outcome(self, result, context, data, step):
        input_value = data.get(self.input_field)

        if self.input_mapping:
            input_value = self.input_mapping.get(input_value)

        result_value = result.value

        if self.result_mapping:
            result_value = self.result_mapping.get(result_value)

        if input_value == result_value:
            return ResultOutcome(outcome_step=step, next_step=self.true_step, reason=f"decision '{result_value}' and input match",
                                 input_data=data, context=context, result=result, value=1)

        return ResultOutcome(outcome_step=step, next_step=self.false_step, reason=f"decision '{result_value})' does not match input '{input_value})'",
                                  input_data=data, context=context, result=result, value=0)
