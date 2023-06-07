from easul.visual import Visual
from easul.tests.example import curb65_score_algorithm
from easul.outcome import ResultOutcome
from easul.algorithm.logic import ScoreResult
from easul.algorithm import FactorMatch
from easul.algorithm.factor import Factor, OperatorFactor
import operator
from easul.expression import OperatorExpression
import logging

from easul.visual.element.score import FactorBars

logging.basicConfig(level = logging.INFO)
LOG = logging.getLogger(__name__)
from unittest.mock import Mock

def test_create_factor_bars():
    step1 = Mock()
    step1.name = "step1"


    visual = Visual(elements=[FactorBars()])
    input_data = {"confusion":"1", "urea":"25","rr":29,"sbp":"90", "dbp":"66","age":"78"}
    result = {"value":2, "matched_factors":[
        {"penalty":1, "title":"Mental confusion","matched_data":"confusion is true"},
        {"penalty":1, "title":"Uremia", "matched_data":"urea is greater than 19"}
    ], "label":"MED", "ranges": { "LOW": (0, 1), "MED":(2,2), "HIGH":(3,5)}, "data":input_data}

    assert visual.render(algorithm=curb65_score_algorithm(), result=result)