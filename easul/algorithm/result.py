from collections import namedtuple
from typing import Optional
from attrs import define, field
import logging
LOG = logging.getLogger(__name__)

Probability = namedtuple("Probability",["probability","label","value"])

@define(kw_only=True, eq=False)
class Result:
    """
    Base result class which at a simple level just returns a value.
    """
    value = field()
    data = field()

    def asdict(self):
        """
        Dictionary representation of the result used to store the object in databases etc.
        Returns:

        """
        return {
            "value": self.value,
            "data": self.data.asdict()
        }

    def __getitem__(self, item):
        if not hasattr(self, item):
            return None

        return getattr(self, item)

    def __eq__(self, other):
        return self.asdict() == other.asdict()

@define(kw_only=True)
class CaseResult(Result):
    """
    Result for case which also includes the case it was matched on (matched_case)
    """
    matched_case = field()

    def __getitem__(self, item):
        if not hasattr(self, item):
            return None

        return getattr(self, item)

@define(kw_only=True, eq=False)
class ClassifierResult(Result):
    """
    Result for classifier which also includes probabilities and the label
    """
    label = field()
    probabilities = field()
    def asdict(self):
        return {
            "value": self.value,
            "label": self.label,
            "probabilities":[p._asdict() for p in self.probabilities],
            "data":self.data.asdict()
        }

    def __eq__(self, other):
        return self.asdict() == other.asdict()

@define(kw_only=True)
class RegressionResult(Result):
    """
    Result for regression which only contains the value
    """
    pass


@define(kw_only=True)
class NullResult(Result):
    """
    Failed or null result
    """
    value:Optional[int] = None
    label = "No result"


@define(kw_only=True)
class DefaultResult(Result):
    """
    Result used when data is missing to output a default result
    """
    label = "Default result"

@define(kw_only=True)
class ScoreResult(Result):
    """
    Score-based result which also contains a list of matched factors, a label for the match and a set of score ranges.
    """
    label = field()
    matched_factors = field(factory=list)
    ranges = field(factory=dict)

    def __repr__(self):
        return f"<ScoreResult matched_factors={self.matched_factors}, value={self.value}, label={self.label}, ranges={self.ranges}>"

    def __str__(self):
        return self.__repr__()

    def asdict(self):
        return {
            "matched_factors":[f.asdict() for f in self.matched_factors],
            "value": self.value,
            "label": self.label,
            "ranges": self.ranges,
            "data": self.data.asdict()
        }