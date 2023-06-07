from unittest.mock import Mock

import pytest


# diabetes data used from https://www4.stat.ncsu.edu/~boos/var.select/diabetes.html a processed version is
# also part of sklearn


@pytest.fixture
def classifier_dataset():
    from easul.tests.example import load_diabetes
    return load_diabetes(raw=True, as_classifier=True)

@pytest.fixture
def regression_dataset():
    from easul.tests.example import load_diabetes
    return load_diabetes(raw=True, as_classifier=False)



@pytest.fixture
def mock_ids(monkeypatch):
    new_id = Mock()
    new_id.side_effect=range(1,500)
    monkeypatch.setattr("easul.util.new_id",new_id)

@pytest.fixture
def complex_plan():
    from easul.tests.example import complex_plan_with_ml
    return complex_plan_with_ml()

