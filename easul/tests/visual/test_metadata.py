"""Visual metadata carrying a live explainer, round-tripped through a plan.

Uses ipso's own ``Visual`` (metadata as an explicit field, per the legacy
ipso-crate design), so no EASUL ``metadata_filename``/dill path is involved.
The explainer inside the metadata must survive so it can explain new rows.
"""
import os

import numpy as np
import pytest

from easul import Metadata, Visual, DatasetMetadata, Prediction, FileMetadata
from easul.algorithm import ClassifierAlgorithm
from easul.tests.example import load_diabetes
from easul.visual.element.overall import Sensitivity
from easul.visual.element.prediction import LimeTablePlot
from lime.lime_tabular import LimeTabularExplainer
from sklearn.linear_model import LogisticRegression

def create_algorithm():
    dataset = load_diabetes(raw=True, as_classifier=True)
    train, test = dataset.train_test_split(train_size=0.75)

    algorithm = ClassifierAlgorithm(
        title="Diabetes progression",
        model=LogisticRegression(max_iter=500),
        schema=dataset.schema,
    )
    algorithm.fit(train)
    return algorithm, test

def test_metadata_is_empty_if_visual_receives_no_parameters():
    algorithm, test = create_algorithm()

    visual = Visual(
        title="Performance",
        algorithm=algorithm,
        elements=[Prediction(), LimeTablePlot(), Sensitivity()],
    )

    assert isinstance(visual.metadata, Metadata)
    assert visual.metadata == {}

def test_metadata_is_computed_from_dataset_if_provided_in_metadata():
    algorithm, train = create_algorithm()
    visual = Visual(
        title="Performance",
        algorithm=algorithm,
        metadata=DatasetMetadata(train),
        elements=[Prediction(), LimeTablePlot(), Sensitivity()],
    )
    metadata = visual.metadata
    assert isinstance(metadata, Metadata)
    assert "lime_explainer" in metadata
    assert "sensitivity" in metadata

def test_metadata_is_computed_if_provided_via_metadata_dataset():
    algorithm, train = create_algorithm()
    visual = Visual(
        title="Performance",
        algorithm=algorithm,
        metadata_dataset=train,
        elements=[Prediction(), LimeTablePlot(), Sensitivity()],
    )
    metadata = visual.metadata
    assert isinstance(metadata, Metadata)
    assert "lime_explainer" in metadata
    assert "sensitivity" in metadata


def test_metadata_is_populated_from_file_if_provided_in_metadata(tmp_path):
    from easul import util

    path = tmp_path / "metadata.pkl"
    path.write_bytes(util.to_serialized({"sensitivity": 0.56, "recall": 0.67}))

    algorithm, train = create_algorithm()
    visual = Visual(
        title="Performance",
        algorithm=algorithm,
        metadata_filename=str(path),
        elements=[Prediction(), LimeTablePlot(), Sensitivity()],
    )

    metadata = visual.metadata
    assert isinstance(metadata, Metadata)
    assert "sensitivity" in metadata
    assert "recall" in metadata

    # Loaded metadata can be saved back.
    metadata.save()
