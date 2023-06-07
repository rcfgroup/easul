import operator

import pandas as pd

from easul.action import ResultStoreAction
from easul.algorithm import StoredAlgorithm
from easul.algorithm.factor import OperatorFactor
from easul.data import DataSchema, DFDataInput
from easul.step import VisualStep
from easul.visual import Visual
from easul.visual.element import Prediction
from easul.visual.element.container import HorizContainer, CardContainer, Container
from easul.visual.element.journey import JourneyMap
from easul.visual.element.overall import RocCurve, Accuracy, BalancedAccuracy, Ppp, Npp, Sensitivity, Matthews, \
    ModelScore
from easul.visual.element.prediction import ProbabilityPlot, LimeTablePlot
from easul.visual.element.overall import Specificity

import os

import numpy as np

EXAMPLE_PATH = os.path.dirname(__file__) + "/support"
DIABETES_FILE = EXAMPLE_PATH + "/diabetes.txt"


def diabetes_progression_algorithm():
    from easul.algorithm import ClassifierAlgorithm
    from sklearn.linear_model import LogisticRegression
    diab_train = diabetes_progression_dataset()

    diab_alg = ClassifierAlgorithm(title="Diabetes progression", model=LogisticRegression(max_iter=500), schema=diab_train.schema)

    diab_alg.fit(diab_train)

    return diab_alg


def diabetes_progression_dataset():
    diab_dset = load_diabetes(raw=True, as_classifier=True)

    diab_train, diab_test = diab_dset.train_test_split(train_size=0.75)
    return diab_train


# *Data Set Characteristics:**

#   :Number of Instances: 442
#
#   :Number of Attributes: First 10 columns are numeric predictive values
#
#   :Target: Column 11 is a quantitative measure of disease progression one year after baseline
#
#   :Attribute Information:
#       - age     age in years
#       - sex
#       - bmi     body mass index
#       - bp      average blood pressure
#       - s1      tc, total serum cholesterol
#       - s2      ldl, low-density lipoproteins
#       - s3      hdl, high-density lipoproteins
#       - s4      tch, total cholesterol / HDL
#       - s5      ltg, possibly log of serum triglycerides level
#       - s6      glu, blood sugar level
#
# Note: Each of these 10 feature variables have been mean centered and scaled by the standard deviation times `n_samples` (i.e. the sum of squares of each column totals 1).
#
# Source URL:
# https://www4.stat.ncsu.edu/~boos/var.select/diabetes.html
#
# For more information see:
# Bradley Efron, Trevor Hastie, Iain Johnstone and Robert Tibshirani (2004) "Least Angle Regression," Annals of Statistics (with discussion), 407-499.
# (https://web.stanford.edu/~hastie/Papers/LARS/LeastAngle_2002.pdf)
def load_diabetes(raw=False, as_classifier=False):
    import pandas as pd

    if raw:
        schema = DataSchema(
            schema={
                "age": {"type": "number", "help": "Age in years"},
                "sex": {"type": "category", "options": {1: "Male", 2: "Female"}, "help": "Gender",
                        "pre_convert": "integer"},
                "bmi": {"type": "number", "help": "Body mass index"},
                "bp": {"type": "number", "help": "Avg blood pressure"},
                "s1": {"type": "number", "help": "tc, total serum cholesterol"},
                "s2": {"type": "number", "help": "ldl, low-density lipoproteins"},
                "s3": {"type": "number", "help": "hdl, high-density lipoproteins"},
                "s4": {"type": "number", "help": "tch, total cholesterol / HDL"},
                "s5": {"type": "number", "help": "ltg, possibly log of serum triglycerides level"},
                "s6": {"type": "number", "help": "glu, blood sugar level"},
                "y": {
                    "type": "number",
                    "help": "disease progression (<1 yr)"
                }
            },
            y_names=["y"],
        )
        df = pd.read_csv(
            DIABETES_FILE, delimiter="\t"
        )
    else:
        schema = DataSchema(
            schema={
                "age": {"type": "number", "help": "Age in years", "min": -1, "max": 1},
                "sex": {"type": "category", "options": {-0.04464: "Male", 0.05068: "Female"}, "help": "Gender",
                        "pre_convert": "integer"},
                "bmi": {"type": "number", "help": "Body mass index", "min": -1, "max": 1},
                "bp": {"type": "number", "help": "Avg blood pressure", "min": -1, "max": 1},
                "s1": {"type": "number", "help": "tc, total serum cholesterol", "min": -1, "max": 1},
                "s2": {"type": "number", "help": "ldl, low-density lipoproteins", "min": -1, "max": 1},
                "s3": {"type": "number", "help": "hdl, high-density lipoproteins", "min": -1, "max": 1},
                "s4": {"type": "number", "help": "tch, total cholesterol / HDL", "min": -1, "max": 1},
                "s5": {"type": "number", "help": "ltg, possibly log of serum triglycerides level", "min": -1, "max": 1},
                "s6": {"type": "number", "help": "glu, blood sugar level", "min": -1, "max": 1},
                "y": {
                    "type": "number",
                    "help": "disease progression (<1 yr)"
                }
            },
            y_names=["y"],
        )

        from sklearn.datasets import load_diabetes

        diabetes = load_diabetes()

        df = pd.DataFrame(data=diabetes.data, columns=diabetes.feature_names)
        df["y"] = diabetes.target

    if as_classifier:
        schema["y"] = {"type": "category", "help": "Boolean flag for disease progression",
                       "pre_convert": "integer", "options": {0: "No progression", 1: "Progression"}}
        df["y"] = df["y"].apply(lambda x: 1 if x > 150 else 0)

    return DFDataInput(data=df, schema=schema)


model_scope_elements = [
    CardContainer(
        title="The rating below is an average of the accuracies, correlation and AUC scores",
        name="rating_card",
        elements=[
            ModelScore(title="What is the model rating (out of 100)"),
            CardContainer(title="The individual aspects of the model can be examined below",
                          name="individual_card",
                          heading_level=5,
                          elements=[
                              HorizContainer(
                                  elements=[
                                      RocCurve(name="roc", title="ROC curve", width=5, height=5),
                                      Container(
                                          elements=[
                                              Accuracy(name="accu", title="How accurate is the model overall?",
                                                       round_dp=1),
                                              BalancedAccuracy(name="bal_accu",
                                                               title="How accurate if the responses were balanced?",
                                                               round_dp=1),
                                              Ppp(name="ppp", title="Positives correctly identified (PPV)",
                                                  round_dp=1),
                                              Npp(name="ppp", title="Negatives correctly identified (NPV)",
                                                  round_dp=1),
                                              Sensitivity(name="sens",
                                                          title="True positives out of identified positives (Sensitivity)",
                                                          round_dp=1),
                                              Specificity(name="specs",
                                                          title="True negatives out of identified negatives (Specificity)",
                                                          round_dp=1),
                                              Matthews(name="matt",
                                                       title="Prediction correlation (Matthews) (between -1 and 1)",
                                                       round_dp=1
                                                       )
                                          ]
                                      )
                                  ]
                              )
                          ]
                          )
        ]
    )
]

row_scope_elements = [
    HorizContainer(elements=[
        CardContainer(
            title="Prediction and probabilities of survival or death",
            elements=[
                HorizContainer(elements=[
                    Prediction(name="pred", title="Prediction", show_label=True, as_value=False,
                               html_class="bg-info",
                               html_tag="h5"),
                    ProbabilityPlot(name="probs", height=4, width=4, title="Probability plot")
                ]),
                CardContainer(
                    title="Explanation of how supplied values affect the likelihood of this prediction?",
                    name="lime_card",
                    heading_level=5,
                    elements=[
                        LimeTablePlot()
                    ])
            ])
    ])
]


def complex_plan():
    from easul.decision import BinaryDecision
    from easul.plan import Plan
    from easul.visual.element.journey import JourneyMap

    from easul.state import State
    from easul.step import EndStep, StartStep, Step, AlgorithmStep, PreStep, VisualStep
    from easul.visual import Visual

    from easul.action import PreRunStateAction

    complex_plan = Plan(title="CAP")
    complex_plan.add_state("admission_state", State(label="admission", default=None))

    complex_plan.add_step("discharge", EndStep(
        title="Discharge",
        actions=[PreRunStateAction(state=complex_plan.get_state("admission_state"), state_value="discharged")]
    ))
    complex_plan.add_step("itu", EndStep(
        title="ITU",
        actions=[PreRunStateAction(state=complex_plan.get_state("admission_state"), state_value="itu")]
    ))

    complex_plan.add_step("admission", StartStep(
        title="Patient admission",
        actions=[PreRunStateAction(state=complex_plan.get_state("admission_state"), state_value="admitted")],
        next_step=complex_plan.get_step("catheter_check")
    ))

    complex_plan.add_step("flowchart", Step(
        title="CAP logic map",
        visual=Visual(
            elements=[
                JourneyMap(route_only=False, start_step="admission")
            ]),
        exclude_from_chart=True
    ))

    complex_plan.add_schema("catheter",
                            DataSchema(
                                schema={
                                    "systolic_bp": {"type": "number"},
                                    "score": {"type": "number"}
                                },
                                y_names=["score"]
                            )
                            )

    from easul.algorithm import ScoreAlgorithm

    complex_plan.add_algorithm("catheter",
                               ScoreAlgorithm(
                                   title="Catheter algorithm",
                                   schema=complex_plan.get_schema("catheter"),
                                   factors=[OperatorFactor(operator=operator.gt, input_field="systolic_bp", value=90,
                                                           penalty=1, title="High systolic BP")]
                               )
                               )
    complex_plan.add_step("catheter_check", AlgorithmStep(
        title="Catheter check",
        actions=[PreRunStateAction(state=complex_plan.get_state("admission_state"), state_value="catheter_check")],
        algorithm=complex_plan.get_algorithm("catheter"),
        source=complex_plan.get_source("catheter"),
        decision=BinaryDecision(
            true_step=complex_plan.get_step("itu"),
            false_step=complex_plan.get_step("discharge")
        )
    ))

    complex_plan.add_step("flowchart", Step(
        title="Diabetes logic map",
        visual=Visual(
            elements=[
                JourneyMap(route_only=False, start_step="admission")
            ]),
        exclude_from_chart=True
    ))

    from easul.source import ConstantSource
    complex_plan.add_source("catheter", ConstantSource(title="Catheter data", data={"systolic_bp": 80}))
    return complex_plan

def complex_plan_with_ml_no_metadata(tempdir):
    plan = _complex_plan_with_ml()
    plan.add_algorithm("progression", StoredAlgorithm(filename=tempdir + "/diabetes.eal",
                                                                      title="Diabetes progression likelihood",
                                                                      definition=diabetes_progression_algorithm
                                                                      ))
    plan.add_visual("model_scope", Visual(
        title="Diabetes model scope",
        algorithm=plan.get_algorithm("progression"),
        elements=model_scope_elements,
        metadata_filename=tempdir+"/test_model.eam",
        metadata_dataset="easul.tests.example.diabetes_progression_dataset"
    ))
    plan.add_visual("row_scope", Visual(
        title="Diabetes row scope",
        algorithm=plan.get_algorithm("progression"),
        elements=row_scope_elements,
        metadata_filename=tempdir + "/test_row.eam",
        metadata_dataset="easul.tests.example.diabetes_progression_dataset"
    ))

    return plan

def _complex_plan_with_ml():
    from easul.decision import BinaryDecision
    from easul.plan import Plan

    from easul.state import State
    from easul.step import EndStep, StartStep, Step, AlgorithmStep, PreStep, VisualStep
    from easul.visual import Visual

    from easul.action import PreRunStateAction

    import os


    complex_plan_with_ml = Plan(title="CAP")
    complex_plan_with_ml.add_state("admission_state", State(label="admission", default=None))
    complex_plan_with_ml.add_state("progression", State(label="progression", default=None))

    complex_plan_with_ml.add_step("discharge", EndStep(
        title="Discharge",
        actions=[PreRunStateAction(state=complex_plan_with_ml.get_state("admission_state"), state_value="discharged")]
    ))
    complex_plan_with_ml.add_step("itu", EndStep(
        title="ITU",
        actions=[PreRunStateAction(state=complex_plan_with_ml.get_state("admission_state"), state_value="itu")]
    ))

    complex_plan_with_ml.add_step("admission", StartStep(
        title="Patient admission",
        actions=[PreRunStateAction(state=complex_plan_with_ml.get_state("admission_state"), state_value="admitted")],
        next_step=complex_plan_with_ml.get_step("catheter_check")
    ))

    complex_plan_with_ml.add_step("flowchart", Step(
        title="CAP logic map",
        visual=Visual(
            elements=[
                JourneyMap(route_only=False, start_step="admission")
            ]),
        exclude_from_chart=True
    ))

    complex_plan_with_ml.add_schema("catheter",
                                    DataSchema(
                                        schema={
                                            "systolic_bp": {"type": "number"},
                                            "score": {"type": "number"}
                                        },
                                        y_names=["score"]
                                    )
                                    )

    complex_plan_with_ml.add_step("progression_low", PreStep(
        title="Diabetes progression low",
        actions=[PreRunStateAction(state=complex_plan_with_ml.get_state("progression"), state_value="low")],
        next_step=complex_plan_with_ml.get_step("discharge")
    ))
    complex_plan_with_ml.add_step("progression_high", PreStep(
        title="Diabetes progression high",
        actions=[PreRunStateAction(state=complex_plan_with_ml.get_state("progression"), state_value="high")],
        next_step=complex_plan_with_ml.get_step("itu")
    ))

    complex_plan_with_ml.add_step("progression_check", AlgorithmStep(
        algorithm=complex_plan_with_ml.get_algorithm("progression"),
        title="Progression ML",
        actions=[
            PreRunStateAction(state=complex_plan_with_ml.get_state("progression"), state_value="pending"),
            ResultStoreAction()
        ],
        decision=BinaryDecision(
            true_step=complex_plan_with_ml.get_step("progression_high"),
            false_step=complex_plan_with_ml.get_step("progression_low")
        ),
        source=complex_plan_with_ml.get_source("progression"),
        visual=complex_plan_with_ml.get_visual("row_scope")
    ))

    from easul.algorithm import ScoreAlgorithm, StoredAlgorithm

    complex_plan_with_ml.add_algorithm("catheter",
                                       ScoreAlgorithm(
                                           title="Catheter algorithm",
                                           schema=complex_plan_with_ml.get_schema("catheter"),
                                           factors=[
                                               OperatorFactor(title="High blood pressure", operator=operator.gt, input_field="systolic_bp", value=90,
                                                              penalty=1)]
                                       )
                                       )
    complex_plan_with_ml.add_step("catheter_check", AlgorithmStep(
        title="Catheter check",
        actions=[
            PreRunStateAction(state=complex_plan_with_ml.get_state("admission_state"), state_value="catheter_check")],
        algorithm=complex_plan_with_ml.get_algorithm("catheter"),
        source=complex_plan_with_ml.get_source("catheter"),
        decision=BinaryDecision(
            true_step=complex_plan_with_ml.get_step("progression_check"),
            false_step=complex_plan_with_ml.get_step("discharge")
        )
    ))

    from easul.source import ConstantSource
    complex_plan_with_ml.add_source("catheter", ConstantSource(title="Catheter data", data={"systolic_bp": 80}))
    complex_plan_with_ml.add_source("progression", ConstantSource(title="Diabetes progression data", data={}))



    complex_plan_with_ml.add_step("flowchart", Step(
        title="Diabetes logic map",
        visual=Visual(
            elements=[
                JourneyMap(route_only=False, start_step="admission")
            ]),
        exclude_from_chart=True
    ))

    return complex_plan_with_ml

def complex_plan_with_ml():
    plan = _complex_plan_with_ml()

    plan.add_algorithm("progression", StoredAlgorithm(filename=EXAMPLE_PATH + "/metadata/diabetes.eal",
          title="Diabetes progression likelihood",
          definition=diabetes_progression_algorithm
      ))

    plan.add_step("overview", VisualStep(
        title="Model",
        visual=plan.get_visual("model_scope")
    ))

    plan.add_visual("model_scope", Visual(
        title="Diabetes model scope",
        algorithm=plan.get_algorithm("progression"),
        elements=model_scope_elements,
        metadata_filename=EXAMPLE_PATH + "/metadata/model_scope.emd",
        metadata_dataset="easul.tests.example.diabetes_progression_dataset"
    ))
    plan.add_visual("row_scope", Visual(
        title="Diabetes row scope",
        algorithm=plan.get_algorithm("progression"),
        elements=row_scope_elements,
        metadata_filename=EXAMPLE_PATH + "/metadata/row_scope.emd",
        metadata_dataset="easul.tests.example.diabetes_progression_dataset"
    ))

    return plan


curb65_schema = DataSchema(
    schema={
        "confusion": {"type": "boolean", "required": True},
        "urea": {"type": "number", "required": True},
        "rr": {"type": "number", "required": True},
        "sbp": {"type": "number", "required": True},
        "dbp": {"type": "number", "required": True},
        "age": {"type": "number", "required": True},
        "score": {"type": "number", "required": True}
    }, y_names=["score"])

prog_input_data = {"age": 59, "sex": 2, "bmi": 32.1, "bp": 101, "s1": 157, "s2": 93.2, "s3": 38, "s4": 4, "s5": 4.9,
                   "s6": 87}
no_prog_input_data = {"age": 23, "sex": 1, "bmi": 20.1, "bp": 78, "s1": 77, "s2": 93.2, "s3": 38, "s4": 4, "s5": 4.9,
                      "s6": 37}


def curb65_score_algorithm():
    from easul.algorithm import logic, factor
    from easul import expression
    import operator

    return logic.ScoreAlgorithm(
        title="CURB65",
        factors=[
            factor.OperatorFactor(penalty=1, operator=operator.eq, value=1, input_field="confusion", title="Confusion"),
            factor.OperatorFactor(penalty=1, operator=operator.gt, value=19, input_field="urea", title="High urea",),
            factor.OperatorFactor(penalty=1, operator=operator.ge, value=30, input_field="rr", title="High respiratory rate"),
            factor.ExpressionFactor(penalty=1, expression=expression.OrExpression(
                expressions=[
                    expression.OperatorExpression(operator=operator.lt, value=90, input_field="sbp"),
                    expression.OperatorExpression(operator=operator.le, value=60, input_field="dbp")
                ]
            ), title="Low blood pressure"
                                    ),
            factor.OperatorFactor(penalty=1, operator=operator.ge, value=65, input_field="age", title="Age >= 65")
        ],
        schema=curb65_schema,
        start_score=0
    )
