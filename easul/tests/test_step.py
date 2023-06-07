from easul import *
from easul.tests.example import curb65_score_algorithm
from easul.visual.element.score import *
from easul.visual.element.container import *
from easul.visual.element.markup import *
# from easul.action import *

curb65_visual = Visual(
  elements = [
      Heading(title="CURB65 used to inform severity", heading_level=4),
          HorizContainer(elements=[
            ScoreValue(name="score", title="", round_dp=0),
            ScoreLabel(name="score_lbl", title="", format="[%s]", round_dp=None)
              ]),
          FactorBars(name="factors", single_block_width= 150, height=150, title="Factors contributing to CURB65"),
FactorTable(name="factor_tab", title="Breakdown and reason for CURB65 scoring"),
          ],
    title="CURB 65 factor"
    )

def test_step_describe_outputs_expected_structure():
    sev_state = State(label="Severity", default=None)
    plow = EndStep(title="Low severity", name="cap_low")
    pmod = EndStep(title="Moderate severity", name="cap_mod")
    phigh = EndStep(title="High severity", name="cap_high")
    step = AlgorithmStep(
        title="Determine pneumonia severity from CURB65",
        source=ConstantSource(title="Severity data", data={"confusion":False}),
        algorithm=curb65_score_algorithm(),
        visual=curb65_visual,
        actions=[
            PreRunStateAction(state_value="pending", state=sev_state),
            ResultStoreAction(send_message=True),
        ],
        decision=SelectCaseDecision(cases=[
            DecisionCase(expression=BetweenExpression(input_field="value", from_value=0, to_value=1),
                         true_step=plow, title="CURB65 0-1"),
            DecisionCase(expression=OperatorExpression(input_field="value", operator=operator.eq, value=2),
                         true_step=pmod, title="CURB65 2"),
            DecisionCase(expression=BetweenExpression(input_field="value", from_value=3, to_value=5),
                         true_step=phigh, title="CURB65 3-5")
        ]
        )
    )
    assert step.describe() == {'actions': [{'type': 'PreRunStateAction'}, {'type': 'ResultStoreAction'}],
 'algorithm': {'title': 'CURB65', 'type': 'ScoreAlgorithm'},
 'decision': {'cases': ['CURB65 0-1', 'CURB65 2', 'CURB65 3-5'],
              'type': 'SelectCaseDecision'},
 'name': None,
 'source': {'title': 'Severity data', 'type': 'ConstantSource'},
 'title': 'Determine pneumonia severity from CURB65',
 'visual': {'title': 'CURB 65 factor', 'type': 'Visual'}}