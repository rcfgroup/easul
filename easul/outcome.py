from attrs import define, field


@define(kw_only=True)
class Outcome:
    """
    Base Outcome class. Output by Decision classes and contains information on the next step (based on the decision),
    the reason for the outcome/decision and context related to the result.
    """
    outcome_step = field()
    next_step = field()
    reason = field()
    context = field(default=None)
    input_data = field(default=None)

    def asdict(self):
        return {
            "outcome_step":self.outcome_step.name,
            "next_step":self.next_step.name if self.next_step else None,
            "reason":self.reason,
            "context":self.context if self.context else {},
            "input_data": self.input_data if type(self.input_data) is dict else self.input_data.asdict() if self.input_data else {}
        }

    def __repr__(self):
        return f"<{self.__class__.__name__ } {self.asdict()}>"

@define(kw_only=True)
class EndOutcome(Outcome):
    """
    Outcome at the end of the patient journey.
    """
    next_step = field(default=None)
    reason = field(default=None)

    def asdict(self):
        return {
            "outcome_step":self.outcome_step.name
        }

@define(kw_only=True)
class ResultOutcome(Outcome):
    """
    Outcome also containing a value and an algorithm result.
    """
    value = field()
    result = field()

    def asdict(self):
        data = super().asdict()
        data.update({
            "result":self.result.asdict(),
            })
        return data

@define(kw_only=True)
class PauseOutcome(Outcome):
    """
    Outcome indicating that system should pause and only continue when pushed.
    """
    pass

@define(kw_only=True)
class FailedOutcome(Outcome):
    """
    Base failed outcome class.
    """
    pass

@define(kw_only=True)
class InvalidDataOutcome(FailedOutcome):
    """
    Decision failed because of invalid data.
    """
    next_step = field(default=None)

@define(kw_only=True)
class MissingDataOutcome(FailedOutcome):
    """
    Decision failed because of missing data.
    """
    next_step = field(default=None)
