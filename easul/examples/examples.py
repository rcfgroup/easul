from easul import *
from easul.tests.example import diabetes_progression_algorithm, EXAMPLE_PATH, model_scope_elements, row_scope_elements
import pandas as pd

def create_example_plan():
    """
    Simple example plan which incorporates a model based on the diabetes data from https://www4.stat.ncsu.edu/~boos/var.select/diabetes.html
    Returns:

    """
    complex_plan_with_ml = Plan(title="Diabetes")
    complex_plan_with_ml.add_state("admission_state", State(label="admission", default=None))
    complex_plan_with_ml.add_state("progression", State(label="progression", default=None))

    complex_plan_with_ml.add_step("discharge", EndStep(
        title="Patient discharged from hospital",
        actions=[PreRunStateAction(state=complex_plan_with_ml.get_state("admission_state"), state_value="discharged")]
    ))
    complex_plan_with_ml.add_step("itu", EndStep(
        title="Intensive treatment unit",
        actions=[PreRunStateAction(state=complex_plan_with_ml.get_state("admission_state"), state_value="itu")]
    ))

    complex_plan_with_ml.add_step("admission", StartStep(
        title="Patient admitted to hospital",
        actions=[PreRunStateAction(state=complex_plan_with_ml.get_state("admission_state"), state_value="admitted")],
        next_step=complex_plan_with_ml.get_step("catheter_check")
    ))

    complex_plan_with_ml.add_step("flowchart", Step(
        title="Diabetes patient journey",
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
        title="Low likelihood of diabetes progression",
        actions=[PreRunStateAction(state=complex_plan_with_ml.get_state("progression"), state_value="low")],
        next_step=complex_plan_with_ml.get_step("discharge")
    ))
    complex_plan_with_ml.add_step("progression_high", PreStep(
        title="High likelihood of diabetes progression",
        actions=[PreRunStateAction(state=complex_plan_with_ml.get_state("progression"), state_value="high")],
        next_step=complex_plan_with_ml.get_step("itu")
    ))

    complex_plan_with_ml.add_step("progression_check", AlgorithmStep(
        algorithm=complex_plan_with_ml.get_algorithm("progression"),
        title="Progression check using ML model",
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

    from easul.algorithm.factor import OperatorFactor
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
        title="Catheter check based on high blood pressure",
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
    complex_plan_with_ml.add_source("catheter", ConstantSource(title="Catheter data", data={}))
    complex_plan_with_ml.add_source("progression", ConstantSource(title="Diabetes progression data", data={}))



    complex_plan_with_ml.add_step("flowchart", Step(
        title="Diabetes logic map",
        visual=Visual(
            elements=[
                JourneyMap(route_only=False, start_step="admission")
            ]),
        exclude_from_chart=True
    ))

    complex_plan_with_ml.add_algorithm("progression", StoredAlgorithm(filename=EXAMPLE_PATH + "/metadata/diabetes.eal",
                                                      title="Diabetes progression likelihood",
                                                      definition=diabetes_progression_algorithm
                                                      ))

    complex_plan_with_ml.add_step("overview", VisualStep(
        title="Model overview visualisation",
        visual=complex_plan_with_ml.get_visual("model_scope")
    ))

    complex_plan_with_ml.add_visual("model_scope", Visual(
        title="Diabetes model scope",
        algorithm=complex_plan_with_ml.get_algorithm("progression"),
        elements=model_scope_elements,
        metadata_filename=EXAMPLE_PATH + "/metadata/model_scope.emd",
        metadata_dataset="easul.tests.example.diabetes_progression_dataset"
    ))
    complex_plan_with_ml.add_visual("row_scope", Visual(
        title="Diabetes row scope",
        algorithm=complex_plan_with_ml.get_algorithm("progression"),
        elements=row_scope_elements,
        metadata_filename=EXAMPLE_PATH + "/metadata/row_scope.emd",
        metadata_dataset="easul.tests.example.diabetes_progression_dataset"
    ))

    return complex_plan_with_ml

def load_data_file(filename:str, limit:Optional[int]=None, indexes:Optional[List[str]]=None):
    """
    Loads an example data file from those provided with EASUL
    Args:
        filename: Filename of file in  easul/example/data
        limit: Optional number of rows to return

    Returns:

    """
    data_path = os.path.dirname(__file__) + "/data"
    data = pd.read_csv(data_path + "/" + filename)

    if indexes:
        data = data.set_index(indexes)
    if limit:
        return data.head(limit)

    return data
