import os

from sklearn.linear_model import LogisticRegression

import easul.algorithm
from easul.algorithm import *

import numpy as np

from easul.algorithm import RegressionResult
import tempfile
import anys

def test_classifier_algorithm_calculates_single_result(classifier_dataset):
    np.random.seed(123)
    train, test = classifier_dataset.train_test_split(train_size=0.25, random_state=0)

    lr = LogisticRegression()

    algo = ClassifierAlgorithm(title="digits", model=lr, schema=classifier_dataset.schema)
    algo.fit(train)
    serialized = easul.util.to_serialized(algo)

    x_test1 = {"age":59,"sex":2,"bmi":32.1,"bp":101,"s1":157,"s2":93.2,"s3":38,"s4":4,"s5":4.9,"s6":87}
    pred1 = algo.single_result(x_test1)

    algo2 = easul.util.from_serialized(serialized)
    assert algo2.single_result(x_test1) == pred1
    assert pred1 == ClassifierResult(label="Progression",value=1, probabilities=[
        Probability(label="No progression",value=0,probability=0.09),
        Probability(label="Progression",value=1,probability=0.91)
    ])


def test_classifier_algorithm_calculates_single_result(regression_dataset):
    np.random.seed(123)
    train, test = regression_dataset.train_test_split(train_size=0.75, random_state=0)

    lr = LogisticRegression()
    algo = RegressionAlgorithm(title="digits", model=lr, schema=regression_dataset.schema)
    algo.fit(train)


    x_test2 = regression_dataset.X_data.iloc[0]
    preds2 = algo.single_result(x_test2)
    assert preds2 == RegressionResult(value=151.0, data=anys.AnyInstance(object))


def test_classifier_algorithm_hash_with_schema_does_not_change(classifier_dataset):
    ds1_train, ds1_test = classifier_dataset.train_test_split(0.25)

    lr = LogisticRegression()
    lr.fit(ds1_train.X, ds1_train.Y)

    algo = ClassifierAlgorithm(title="digits", model=lr, schema=classifier_dataset.schema)
    digest = algo.unique_digest

    pa_serial = util.to_serialized(algo)
    pa_unserial = util.from_serialized(pa_serial)

    assert pa_unserial.unique_digest == digest

def test_classifier_help_returned_as_dict(classifier_dataset):
    ds1_train, ds1_test = classifier_dataset.train_test_split(0.25)

    lr = LogisticRegression()
    lr.fit(ds1_train.X, ds1_train.Y)

    algo = ClassifierAlgorithm(title="digits", model=lr, schema=classifier_dataset.schema)

    assert algo.help == {"type":"LogisticRegression"}

def test_algorithm_can_be_stored_and_retrieved(classifier_dataset):
    ds1_train, ds1_test = classifier_dataset.train_test_split(0.25)

    lr = LogisticRegression()
    lr.fit(ds1_train.X, ds1_train.Y)

    algo = ClassifierAlgorithm(title="digits", model=lr, schema=classifier_dataset.schema)
    f = tempfile.mktemp()
    util.save_data(f,algo)

    algo2 = util.load_data(f)
    assert algo == algo2
    os.unlink(f)

def test_file_algorithm_will_return_algorithm_from_file(classifier_dataset):
    x_test1 = {"age": 59, "sex": 2, "bmi": 32.1, "bp": 101, "s1": 157, "s2": 93.2, "s3": 38, "s4": 4, "s5": 4.9,
               "s6": 87}

    algo = algo_definition()

    f = tempfile.mktemp()
    util.save_data(f, algo)

    algo2 = StoredAlgorithm(title="stored algorithm", filename=f, definition="easul.tests.algorithm.test_predictive.algo_definition")
    os.unlink(f)

    assert algo == algo2._algorithm

    assert algo.single_result(x_test1) == algo2.single_result(x_test1)
    assert algo.schema == algo2.schema

def algo_definition():
    np.random.seed(123)
    from easul.tests.example import load_diabetes
    dataset = load_diabetes(raw=True, as_classifier=True)
    ds1_train, ds1_test = dataset.train_test_split(0.25)

    lr = LogisticRegression()
    lr.fit(ds1_train.X, ds1_train.Y)

    algo = ClassifierAlgorithm(title="digits", model=lr, schema=dataset.schema)
    return algo