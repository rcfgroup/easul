from easul.algorithm import StoredAlgorithm

import logging

from easul.tests.example import complex_plan_with_ml

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(asctime)s %(message)s")
LOG = logging.getLogger(__name__)
import anys
import numpy as np
from unittest.mock import ANY
ANYTHING = anys.AnyInstance(object)

METADATA_KEYS = {
    "model_scope": {
        "algorithm_digest":anys.ANY_STR,
        "model_score":ANY,
        "fpr":ANY,
        "tpr":ANY,
        "roc_auc":ANY,
        "accuracy":ANY,
        "balanced_accuracy":ANY,
        "ppp":ANY,
        "npp":ANY,
        "sensitivity":ANY,
        "specificity":ANY,
        "matthews":ANY,
    },
    "row_scope":{"algorithm_digest":ANY, "lime_explainer":anys.ANY_DICT}}

def generate_test_models():
    plans = {"cap":complex_plan_with_ml()}

    np.random.seed(321)
    for plan_name, plan in plans.items():
        for algo_name, algorithm in plan.algorithms.items():
            if not isinstance(algorithm, StoredAlgorithm):
                continue

            algorithm.update_from_definition()

            algorithm.save_to_file()

        for visual_name, visual in plan.visuals.items():
            visual.calculate_metadata()
            visual.metadata.save()

