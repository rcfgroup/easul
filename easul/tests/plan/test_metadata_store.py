from unittest import mock
import os
import logging
import numpy as np
from easul.plan.repo import PlanRepository

logging.basicConfig(level=logging.INFO)

LOG = logging.getLogger(__name__)
from easul import util
from tempfile import TemporaryDirectory

import pytest

def test_plan_repository_retrieved_and_stored_correctly():
    tempdir = TemporaryDirectory(prefix="easul")
    plan_path = tempdir.name

    from easul.tests.example import complex_plan_with_ml_no_metadata

    plan = complex_plan_with_ml_no_metadata(plan_path)

    ms_visual = plan.visuals["model_scope"]
    rs_visual = plan.visuals["row_scope"]

    assert ms_visual.metadata.loaded_from is None
    assert rs_visual.metadata.loaded_from is None


    repo = PlanRepository(plan)
    repo.store_algorithms()
    repo.store_metadata()

    plan2 = complex_plan_with_ml_no_metadata(plan_path)

    ms_visual2 = plan2.visuals["model_scope"]
    rs_visual2 = plan2.visuals["row_scope"]

    assert ms_visual2.metadata.loaded_from == ms_visual2.metadata_filename
    assert rs_visual2.metadata.loaded_from == rs_visual2.metadata_filename

    for k,v in ms_visual2.metadata.items():
        assert np.array_equal(ms_visual2.metadata[k], v)

    assert ms_visual2.metadata.algorithm == ms_visual2.metadata.algorithm
    tempdir.cleanup()




