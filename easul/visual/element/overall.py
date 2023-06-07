from abc import abstractmethod

from attr import field, define
from scipy.stats import pearsonr

from easul.error import VisualDataMissing
from easul.visual.element import FigureElement, ValueElement, MODEL_SCOPE
from easul.visual.element.container import HorizContainer

class RocCurve(FigureElement):
    scope = MODEL_SCOPE
    @classmethod
    def is_correct_algorithm(cls, algorithm):
        from easul.algorithm import PredictiveAlgorithm, PredictiveTypes
        return isinstance(algorithm, PredictiveAlgorithm) and algorithm.model_type == PredictiveTypes.CLASSIFICATION

    def generate_metadata(self, algorithm, dataset, **kwargs):
        from sklearn import metrics

        probs = algorithm.model.predict_proba(dataset.X)
        preds = probs[:, 1]
        fpr, tpr, _ = metrics.roc_curve(dataset.Y, preds)
        roc_auc = metrics.auc(fpr, tpr)

        return {"fpr": fpr, "tpr": tpr, "roc_auc":roc_auc}

    def _create_figure(self, algorithm, visual, **kwargs):
        if visual.metadata.init is False:
            raise AttributeError("Cannot create element if metadata not initialised")

        figure = self._new_figure()

        metrics = visual.metadata

        ax = figure.add_subplot()
        ax.plot(metrics["fpr"], metrics["tpr"], label='AUC = %0.2f' % metrics["roc_auc"])
        ax.legend(loc='lower right')

        ax.set_xlabel('True Positive Rate', fontsize=14)
        ax.set_ylabel('False Positive Rate', fontsize=14)

        return figure

class ClassificationValueElement(ValueElement):
    scope = MODEL_SCOPE

    @classmethod
    def is_correct_algorithm(cls, algorithm):
        from easul.algorithm import PredictiveAlgorithm, PredictiveTypes
        return True if isinstance(algorithm, PredictiveAlgorithm) and algorithm.model_type == PredictiveTypes.CLASSIFICATION else False

    def retrieve_value(self, visual=None, **kwargs):
        if self.metadata_type not in visual.metadata:
            raise VisualDataMissing(self, "metadata")

        return visual.metadata.get(self.metadata_type)

    @abstractmethod
    def calculate_value(self, algorithm, dataset):
        pass

    def generate_metadata(self, algorithm, dataset, **kwargs):
        return {self.metadata_type:self.calculate_value(algorithm, dataset)}

@define(kw_only=True)
class Accuracy(ClassificationValueElement):
    help = "Show accuracy of algorithm result"
    scope = "prediction-based algorithms"
    start_range = 0
    end_range = 1
    step_size = 0.1
    suffix = field(default="%")
    expression = field(default="value *100")

    def calculate_value(self, algorithm, dataset):
        return algorithm.model.score(dataset.X, dataset.Y)

    @classmethod
    def is_correct_algorithm(cls, algorithm):
        from easul.algorithm import PredictiveAlgorithm
        return isinstance(algorithm, PredictiveAlgorithm)


class BalancedAccuracy(Accuracy):
    help = "Show balanced accuracy of algorithm result"

    def calculate_value(self, algorithm, dataset):
        from sklearn.metrics import balanced_accuracy_score
        y_pred = algorithm.model.predict(dataset.X)
        return balanced_accuracy_score(dataset.Y, y_pred, adjusted=True)


class Matthews(ClassificationValueElement):
    help = "Show Matthew's"
    scope = "prediction-based algorithms"
    start_range = -1
    end_range = 1
    step_size = 0.2

    def calculate_value(self, algorithm, dataset):
        from sklearn import metrics
        preds = algorithm.model.predict(dataset.X)
        return metrics.matthews_corrcoef(dataset.Y, preds)

@define(kw_only=True)
class FalseValue(ClassificationValueElement):
    help = "Show % false values from algorithm result"
    scope = "prediction-based algorithms"
    start_range = 0
    end_range = 100
    step_size = 10
    suffix = field(default="%")

    def calculate_value(self, algorithm, dataset):
        preds = algorithm.model.predict(dataset.X)

        fv = 0

        for idx, pred in enumerate(preds):
            fv+=self._compare_actual_and_predicted(dataset.Y[idx], pred)

        tests = dataset.dataset.shape[0]
        return (fv/tests) * 100

    @abstractmethod
    def _compare_actual_and_predicted(self, actual, predicted):
        pass

class FalseNegatives(FalseValue):
    help = " % false negatives from algorithm result"

    def _compare_actual_and_predicted(self, actual, predicted):
        return 1 if predicted == 0 and actual == 1 else 0


class FalsePositives(FalseValue):
    help = "Show % false positives from algorithm result"

    def _compare_actual_and_predicted(self, actual, predicted):
        return 1 if predicted == 1 and actual == 0 else 0

@define(kw_only=True)
class SSValue(ClassificationValueElement):
    start_range = 0
    end_range = 100
    step_size = 10
    suffix = field(default="%")


    def _true_negative(self, actual, pred):
        return 1 if pred == 0 and actual==0 else 0

    def _false_negative(self, actual, pred):
        return 1 if pred == 0 and actual == 1 else 0

    def _true_positive(self, actual, pred):
        return 1 if pred == 1 and actual == 1 else 0

    def _false_positive(self, actual, pred):
        return 1 if pred == 1 and actual == 0 else 0

    numerator_fn = None
    part_denom_fn = None

    def calculate_value(self, algorithm, dataset):
        preds = algorithm.model.predict(dataset.X)


        numer = 0
        part_denom = 0

        for idx, pred in enumerate(preds):
            numer += self.numerator_fn(dataset.Y[idx], pred)
            part_denom += self.part_denom_fn(dataset.Y[idx], pred)

        if numer == 0 and part_denom == 0:
            import logging
            logging.warning("Numerator and denominator are both zero in " + self.__class__.__name__)
            return ""

        return (numer / (numer+part_denom)) * 100

class ConfusionMatrix(FigureElement):
    def generate_metadata(self, algorithm, dataset, **kwargs):
        from sklearn import metrics

        y_pred = algorithm.model.predict(dataset.X)

        return {"confusion_matrix":metrics.confusion_matrix(dataset.Y, y_pred)}

    def _create_figure(self, algorithm, **kwargs):
        if self.layout.metadata.init is False:
            raise AttributeError("Cannot create element if metadata not initialised")

        from sklearn.metrics import ConfusionMatrixDisplay

        cmd = ConfusionMatrixDisplay(self.layout.metadata["confusion_matrix"])
        return cmd.plot().figure_


class Ppp(SSValue):
    help = "Show positive predictive power (% predicted positive which are actually positive)"

    numerator_fn = SSValue._true_positive
    part_denom_fn = SSValue._false_positive


class Npp(SSValue):
    help = "Show negative predictive power (% predicted negative which are actually negative)"

    numerator_fn = SSValue._true_negative
    part_denom_fn = SSValue._false_negative


class Sensitivity(SSValue):
    help = "Show sensitivity (% correctly positive out of all positives)"

    numerator_fn = SSValue._true_positive
    part_denom_fn = SSValue._false_negative


class Specificity(SSValue):
    help = "Show specificity (% correctly negative out of all negatives)"

    numerator_fn = SSValue._true_negative
    part_denom_fn = SSValue._false_positive


@define(kw_only=True)
class MultiValueContainer(HorizContainer):
    metric_types = {}
    elements = field(init=False)

    @elements.default
    def add_elements_to_mvc(self):
        elements = []
        for mname, mlabel in self.metric_types.items():
            elements.append(ValueElement(title=mlabel, name=self.name + "__" + mname))
        return elements

    def render_content_children(self, container, algorithm, input_data=None, **kwargs):
        metadata = self.layout.metadata

        for mname, mlabel in self.metric_types.items():
            ele = self.layout.get_element(self.name + "__" + mname)
            ele.value = metadata[mname]

        return super().render_content_children(container, algorithm=algorithm, input_data=input_data, **kwargs)

class Correlation(MultiValueContainer):
    scope = MODEL_SCOPE

    metric_types = {"r2": "R<sup>2</sup>", "p_range": "p-value"}

    @classmethod
    def is_correct_algorithm(cls, algorithm):
        from easul.algorithm import RegressionAlgorithm
        return isinstance(algorithm, RegressionAlgorithm)

    def prepare_element(self, **kwargs):
        super().prepare_element(**kwargs)
        r2_element = self.layout.get_element(self.name + "__r2")
        r2_element.start_range = 0
        r2_element.end_range = 1
        r2_element.step_size = 0.1

    def generate_metadata(self, algorithm, dataset, **kwargs):
        Y_actual = dataset.Y
        Y_pred = algorithm.model.predict(dataset.X)

        r, p_value = pearsonr(Y_actual, Y_pred)

        return {"r2":(r * r), "p_range":determine_p_range(p_value)}


def determine_p_range(p_value):
    p_sig_chk = [10 ** (p_sig * -1) for p_sig in range(6, 2,-1)]
    p_sig_chk.append(0.05)

    for p_sig in p_sig_chk:
        if p_value < p_sig:
            return f"<{p_sig}"

    return f"={p_value:.3f}"

class ModelScore(ClassificationValueElement):
    start_range = 0
    end_range = 100
    step_size = 10

    def calculate_value(self, algorithm, dataset):
        from sklearn import metrics
        y_pred = algorithm.model.predict(dataset.X)
        y_probs = algorithm.model.predict_proba(dataset.X)
        y_pos_probs = y_probs[:, 1]

        accuracy = metrics.accuracy_score(dataset.Y, y_pred)
        bal_accuracy = metrics.balanced_accuracy_score(dataset.Y, y_pred, adjusted=True)
        mcorr = metrics.matthews_corrcoef(dataset.Y, y_pred)


        fpr, tpr, _ = metrics.roc_curve(dataset.Y, y_pos_probs)
        roc_auc = metrics.auc(fpr, tpr)

        #TODO not sure this is full working

        score = accuracy + bal_accuracy + ((mcorr + 1) / 2) + roc_auc

        return int((score/4) * 100)


from sklearn.metrics import precision_score, recall_score


class Precision(ClassificationValueElement):

    def calculate_value(self, algorithm, dataset):
        y_pred = algorithm.model.predict(dataset.X)

        return precision_score(dataset.Y, y_pred)

import logging
LOG = logging.getLogger(__name__)
class Recall(ClassificationValueElement):

    def calculate_value(self, algorithm, dataset):
        y_pred = algorithm.model.predict(dataset.X)

        return recall_score(dataset.Y, y_pred)





