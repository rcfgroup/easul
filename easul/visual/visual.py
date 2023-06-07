from collections import UserDict

from attrs import define, field

import logging

from easul.error import StepDataError
from easul.step import ActionEvent
from easul.visual.render import PlainRenderer
from easul import util

LOG = logging.getLogger(__name__)

class Metadata(UserDict):
    def __init__(self, algorithm=None, visual=None):
        super().__init__({})
        self.visual = visual
        self.algorithm = algorithm
        self.init = False

    def calculate(self, dataset):
        if not self.visual:
            raise AttributeError("Cannot calculate metadata as instance has not been called with Visual object")

        metadata = {}

        for element in self.visual.elements:
            element_metadata = element.generate_metadata(algorithm=self.algorithm, dataset=dataset)

            if element_metadata:
                metadata.update(element_metadata)

        metadata["algorithm_digest"] = self.algorithm.unique_digest

        self.init = True
        self.data.update(metadata)


@define(kw_only=True)
class Visual:
    """
    Wrap visual elements and optionally an algorithm related metadata.
    Also includes rendering of the HTML and automatic loading/calculation of metadata.
    """
    elements = field()
    title = field(default=None)
    metadata = field(default=None, init=False)
    metadata_filename = field(default=None)
    algorithm = field(default=None)
    metadata_dataset = field(default=None)

    def describe(self):
        return {
            "title": self.title,
            "type": self.__class__.__name__
        }

    def __attrs_post_init__(self):
        self.metadata = self._create_metadata()

    def _create_metadata(self):
        if self.metadata_filename:
            filename = self.metadata_filename

            metadata = FileMetadata(filename=filename, algorithm=self.algorithm, visual=self)

            try:
                metadata.load()
            except FileNotFoundError:
                LOG.warning("Unable to load metadata - not calculating")

        else:
            metadata = Metadata(algorithm=self.algorithm, visual = self)

        return metadata

    def calculate_metadata(self):
        if self.algorithm:
            if not self.metadata_dataset:
                LOG.warning("Could not calculate algorithm metadata as no 'metadata_dataset' was provided to visual")
        self.metadata.calculate(util.string_to_function(self.metadata_dataset))

    def generate_context(self, input_data, **kwargs):
        result = {}
        for element in self.flattened_elements:
            if not hasattr(element,"generate_context"):
                continue

            ctx = element.generate_context(algorithm=self.algorithm, input_data=input_data, visual=self, **kwargs)
            if not ctx:
                continue

            result.update(ctx)

        return result

    def render(self, driver=None, step=None, steps=None, result=None, context=None, renderer=None, **kwargs):
        if not renderer:
            renderer = PlainRenderer()

        if step and hasattr(step,"run_logic"):
            try:
                cl_step = driver._client.get_step(step.name, journey_id=driver.journey_id)
            except ValueError:
                raise StepDataError(driver.journey, step.name)

            # if not cl_step:
            #     raise SystemError(f"Outcome for reference '{driver.journey['reference']}' and step '{step.name}' does not exist")
            result = None
            context = None

            if cl_step:
                outcome = cl_step.get("outcome",{})
                if outcome:
                    result = outcome.get("result")
                    context = outcome.get("context")

        if self.metadata.algorithm:
            algorithm = self.metadata.algorithm
        else:
            algorithm = step.algorithm if hasattr(step,"algorithm") else None

        if "algorithm" not in kwargs:
            kwargs["algorithm"] = algorithm

        return renderer.create(visual=self, driver=driver, steps=steps, step=step, result=result, context=context,
                              **kwargs)

    @property
    def flattened_elements(self):
        return Visual._get_nested_elements(self)

    @classmethod
    def _get_nested_elements(cls, element):
        if hasattr(element, "elements") is False:
            return [element]

        elements = []

        for sub_element in element.elements:
            elements.extend(cls._get_nested_elements(sub_element))

        return elements

class FileMetadata(Metadata):
    def __init__(self, filename, algorithm, *args, **kwargs):
        super().__init__(algorithm, *args, **kwargs)
        self.filename = filename
        self.loaded_from = None

    def load(self):
        with open(self.filename, "rb") as infile:
            obj_data = infile.read()

        self.data = util.from_serialized(obj_data)

        LOG.debug(f"Loaded metadata from '{self.filename}'")

        self.init = True
        self.loaded_from = self.filename

    def save(self):
        if self.init is False:
            raise ValueError("Not initialised, you must load or calculate metadata to save it")

        with open(self.filename, "wb") as outfile:
            outfile.write(util.to_serialized(self.data))
