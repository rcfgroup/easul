import os

from sklearn.linear_model import LogisticRegression
from easul.tests.example import prog_input_data
from easul.algorithm import ClassifierAlgorithm
from easul.visual import Visual, FileMetadata, Metadata
import numpy as np
import logging

from easul.visual.element import Container, Prediction
from easul.visual.element.overall import Accuracy, Correlation
from easul.visual.element.prediction import LimeTablePlot

LOG = logging.getLogger(__name__)
import lime
import tempfile

def test_simple_visual_will_generate_metadata(classifier_dataset):
    np.random.seed(123)

    lr = LogisticRegression()

    algo = ClassifierAlgorithm(title="digits", model=lr, schema=classifier_dataset.schema)

    train, test = classifier_dataset.train_test_split(train_size=0.25,random_state=0)

    algo.fit(train)

    visual = Visual(elements=[
        Accuracy(name="accu", title="How accurate is the model?",round_dp= 1),
        Correlation(name="corr", title="How correlated are predictions?")
    ], algorithm=algo, metadata_dataset = train)

    visual.calculate_metadata()

    assert visual.metadata.algorithm == algo
    assert list(visual.metadata.keys()) == ['accuracy','r2','p_range', 'algorithm_digest']

def test_visual_returns_flattened_elements_including_multi_value_elements():
    element1 = Accuracy(name="accu", title="How accurate is the model?", round_dp=1),
    element2 = Correlation(name="corr", title="How correlated are predictions?")
    element3 = Prediction(name="pred", title="Prediction")

    visual = Visual(elements=[
        element1,
        element2,
        Container(name="cont", elements = [
            element3
        ])
    ])

    assert visual.flattened_elements == [element1, element2.elements[0], element2.elements[1], element3]


def test_explainer_visual_will_generate_metadata(classifier_dataset):
    np.random.seed(123)


    lr = LogisticRegression()

    algo = ClassifierAlgorithm(title="digits", model=lr, schema=classifier_dataset.schema)

    train, test = classifier_dataset.train_test_split(train_size=0.25,random_state=0)

    algo.fit(train)

    visual = Visual(elements=[
        LimeTablePlot(title="Contributions")
    ], algorithm=algo, metadata_dataset=train)
    visual.calculate_metadata()

    assert list(visual.metadata.keys()) == ['lime_explainer','algorithm_digest']
    assert visual.metadata.algorithm == algo

def test_file_metadata_will_load_and_save(classifier_dataset):
    np.random.seed(123)
    visual = Visual(elements=[
        LimeTablePlot(title="Contributions")
    ])

    lr = LogisticRegression()

    algo = ClassifierAlgorithm(title="digits", model=lr, schema=classifier_dataset.schema)

    train, test = classifier_dataset.train_test_split(train_size=0.25, random_state=0)

    algo.fit(train)

    filename = tempfile.mktemp()
    file_md = FileMetadata(algorithm=algo, visual = visual, filename = filename)

    file_md.calculate(train)
    file_md.save()

    metadata2 = FileMetadata(algorithm=algo, visual =visual, filename = filename)
    metadata2.load()


    os.unlink(filename)

    assert isinstance(metadata2["lime_explainer"], lime.lime_tabular.LimeTabularExplainer)

def test_visual_will_render_html(classifier_dataset):
    np.random.seed(123)

    lr = LogisticRegression()

    algo = ClassifierAlgorithm(title="digits", model=lr, schema=classifier_dataset.schema)

    train, test = classifier_dataset.train_test_split(train_size=0.25,random_state=0)

    algo.fit(train)

    visual = Visual(elements=[
        LimeTablePlot(title="Contributions")
    ], algorithm=algo, metadata_dataset=train)
    visual.metadata.calculate(train)
    context = visual.generate_context(prog_input_data)
    html = visual.render(algorithm=algo, context=context)
    assert html
