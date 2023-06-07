from abc import abstractmethod

from attr import define, field

from easul.algorithm import PredictiveTypes
from easul.error import VisualDataMissing

from easul.visual.element import Element, FigureElement, TrafficLightSwatch, LIST_TYPES, MODEL_SCOPE, \
    ROW_SCOPE, EITHER_SCOPE
from easul.data import SingleDataInput, create_input_dataset, get_field_options_from_schema
from easul.util import get_range_from_discrete_name, get_text_from_range
import re


class ExplainerMixin:
    explainer_type = ""

    @abstractmethod
    def _create_explainer(self, algorithm):
        pass

class ShapExplainerMixin(ExplainerMixin):
    explainer_type = "shap"
    sample_size = 100

    def _create_explainer(self, algorithm):
        import shap

        X = shap.utils.sample(algorithm.dataset.X, self.get_setting("sample_size",100))

        feature_names = [algorithm.schema[x_name].get("help") for x_name in algorithm.schema.x_names]
        return shap.Explainer(algorithm.model.predict, masker=X, feature_names = feature_names)

class ShapBeeswarm(ShapExplainerMixin, FigureElement):
    scope = MODEL_SCOPE
    help = "Show SHAPley beeswarm plot for model"

    @classmethod
    def is_correct_algorithm(cls, algorithm):
        from easul.algorithm import PredictiveAlgorithm
        return isinstance(algorithm, PredictiveAlgorithm)

    def _create_figure(self, algorithm, input_data):
        from matplotlib import pyplot as plot
        fig = plot.figure(self.name, clear=True)

        explainer = self._explainer

        shap_values = explainer(algorithm.dataset.X)

        import shap

        shap.plots.beeswarm(shap_values, show=False)
        return plot.gcf()

class ShapWaterfall(ShapExplainerMixin, FigureElement):
    scope = ROW_SCOPE
    help = "Show SHAPley waterfall plot for input data"

    @classmethod
    def is_correct_algorithm(cls, algorithm):
        from easul.algorithm import PredictiveAlgorithm
        return isinstance(algorithm, PredictiveAlgorithm)

    def _create_figure(self, algorithm, input_data):
        from matplotlib import pyplot as plot
        fig = plot.figure(self.name, clear=True)

        explainer = self._explainer
        ds = create_input_dataset(input_data, algorithm.schema)

        shap_values = explainer(ds.X)

        shap.plots.waterfall(shap_values[0], show=False)
        return plot.gcf()

class ShapPlot(ShapExplainerMixin, FigureElement):
    avail_settings = {
        "scope":{"type":"string","help":"Scope of data to use to produce plot - model (use all model data) or row (single set of values)","default":"input"}
    }
    scope = EITHER_SCOPE
    help = "Show SHAPley plot for either input data or model"

    @classmethod
    def is_correct_algorithm(cls, algorithm):
        from easul.algorithm import PredictiveAlgorithm
        return isinstance(algorithm, PredictiveAlgorithm)

    def _create_figure(self, algorithm, input_data):
        from matplotlib import pyplot as plot
        plot.figure(self.name, clear=True)
        explainer = self._explainer

        if self.scope == MODEL_SCOPE:
            shap_values = explainer(algorithm.dataset.X)
        else:
            ds = create_input_dataset(input_data, algorithm.schema)
            shap_values = explainer(ds.X)

        shap.plots.bar(shap_values, show=False)
        return plot.gcf()

class LimeExplainerMixin(ExplainerMixin):
    explainer_type = "lime"

    def _create_explainer(self, algorithm, dataset):
        from easul.algorithm import ClassifierAlgorithm
        if isinstance(algorithm, ClassifierAlgorithm):
            mode = "classification"
            class_names = get_field_options_from_schema(dataset.schema.y_names[0], dataset.schema)
        else:
            mode = "regression"
            class_names = None

        import lime.lime_tabular

        cat_features = dataset.schema.filter_names(criteria={"type": "list"})
        cat_feature_idxs = [dataset.schema.x_names.index(f) for f in cat_features]
        return lime.lime_tabular.LimeTabularExplainer(dataset.X, feature_names=dataset.schema.x_names,
                                                      categorical_features=cat_feature_idxs,
                                                      mode=mode, class_names = class_names)



class ProbabilityPlot(FigureElement):
    scope = ROW_SCOPE
    help = "Show bar plot for predicted probabilities for each option possible in a classification model"

    @classmethod
    def is_correct_algorithm(cls, algorithm):
        from easul.algorithm import PredictiveAlgorithm, PredictiveTypes
        return isinstance(algorithm, PredictiveAlgorithm) and algorithm.model_type == PredictiveTypes.CLASSIFICATION

    def _create_figure(self, result, **kwargs):
        fig = self._new_figure()

        if not result:
            raise VisualDataMissing(self,scope="result")

        probs = result["probabilities"]

        y_options = [y["label"] for y in probs]

        ax = fig.add_subplot()
        ax.bar([y["label"] for y in probs], [y["probability"] for y in probs])


        ax.margins(0.2, tight=False)

        ax.set_xticklabels(y_options, rotation=90)
        return fig


@define(kw_only=True)
class LimeTablePlot(LimeExplainerMixin, Element):
    html_template = "lime_table_plot.html"
    scope = ROW_SCOPE
    help = "Show LIME table plot showing influence of each variable on the prediction"

    headings = {
        "label": "Label",
        "name": "Name",
        "value": "Value",
        "range": "Range",
        "effect_size": "Size of effect",
        "effect": "Effect"
    }

    @classmethod
    def is_correct_algorithm(cls, algorithm):
        from easul.algorithm import PredictiveAlgorithm
        return isinstance(algorithm, PredictiveAlgorithm)

    def generate_context(self, algorithm, input_data, visual, **kwargs):
        context = {}

        if not algorithm:
            raise VisualDataMissing(self, "algorithm")

        dset = algorithm.create_input_dataset(data=input_data)

        y_info = algorithm.schema.filter(include_x=False, include_y=True)
        y_details = list(y_info.values())[0]

        predict_fn = algorithm.model.predict_proba if y_details["type"] in LIST_TYPES else algorithm.model.predict

        if not "lime_explainer" in visual.metadata:
            raise VisualDataMissing(self,"metadata")

        exp = visual.metadata["lime_explainer"].explain_instance(dset.X[0], predict_fn)

        dm = exp.domain_mapper

        if y_details["type"] in LIST_TYPES:
            options = get_field_options_from_schema(algorithm.schema.y_names[0], algorithm.schema)

            prediction = algorithm.model.predict(dset.X)
            option_label = options[prediction[0]]
            context["prediction_label"] = option_label

        exp_list = exp.as_list()
        lime_values = sorted([abs(x[1]) for x in exp_list], reverse=True)
        highest_lime = lime_values[0]

        reasons = []
        for disc_feat_name, lime_value in exp_list:
            fidx = dm.discretized_feature_names.index(disc_feat_name)
            positive = True if lime_value > 0 else False

            feature_name = dm.exp_feature_names[fidx]
            if isinstance(lime_value, str):
                continue

            if isinstance(lime_value, float):
                lime_value_str = format(lime_value, ".2f")

            feature_name = re.sub("=+.", "", feature_name)
            feature_info = dset.schema.get(feature_name, {})
            rng = get_range_from_discrete_name(disc_feat_name, feature_name)
            lime_abs = abs(lime_value)
            reason = {
                "label": feature_info.get("help", feature_name),
                "name": feature_name,
                "value": dm.feature_values[fidx],
                "range": get_text_from_range(rng, lambda x: x),
                "effect_size": lime_value_str,
                "positive": positive,
                "lime_pc": int((lime_abs / highest_lime) * 100)
            }
            reasons.append(reason)

        context["reasons"] = reasons

        return {"lime_table_plot": context}

    def _get_context(self, context, **kwargs):
        if not context:
            raise VisualDataMissing(self, "context")

        lime_context = context.get(self.metadata_type)
        if not lime_context:
            raise VisualDataMissing(self,"context")

        lime_context.update({
            "green_colour": TrafficLightSwatch.GREEN.get_web(),
            "red_colour": TrafficLightSwatch.RED.get_web()
        })

        return lime_context

    def generate_metadata(self, algorithm, dataset, **kwargs):
        return {
            "lime_explainer": self._create_explainer(algorithm, dataset)
        }


