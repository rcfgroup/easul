from abc import abstractmethod
from typing import Dict

from attr import define, field
from dominate.tags import *
from stringcase import snakecase

from easul.error import VisualDataMissing
from easul.util import Utf8EncodedImage
from easul.visual.render import from_html_template
from easul.visual.draw.style import suggest_text_color_from_fill

LIST_TYPES = ["options","list","category"]

MODEL_SCOPE = "model"
ROW_SCOPE = "row"
EITHER_SCOPE = "either"
import logging
LOG = logging.getLogger(__name__)

class Html:
    def __init__(self):
        self._elements = []

    def start_element(self, tag, attrs=None):
        if attrs:
            attrs = [k + "=\"" + (v if v else "") +"\"" for k,v in attrs.items()]
        else:
            attrs = []

        attr_list = " ".join(attrs)

        self._elements.append(f"<{tag} {attr_list}>")

    def end_element(self, tag):
        self._elements.append(f"</{tag}>")

    def add_text_element(self, tag, text, attrs=None):
        self.start_element(tag, attrs)
        self._elements.append(text)
        self.end_element(tag)

    def __repr__(self):
        return "".join(self._elements)

    def append(self, element):
        self._elements.append(element)

    def add_element(self, tag, attrs):
        attrs = [k + "=\"" + v + "\"" for k, v in attrs.items()]
        attr_list = " ".join(attrs)

        self._elements.append(f"<{tag} {attr_list} />")

@define(kw_only=True)
class Element:
    """Base element which provides initial logic to handle elements in a Layout
    """
    name = field(default="untitled")
    help = field(default="")
    title = field(default="Untitled")
    fill_container = field(default=False)
    html_template = None
    style = field(default=None)
    html_class = field(default="")
    html_tag = field(default="h5")

    @property
    def metadata_type(self):
        return snakecase(self.__class__.__name__)

    @classmethod
    def is_correct_algorithm(cls, algorithm):
        return True


    def create(self, *args, **kwargs):
        context = self._get_context(**kwargs)
        return from_html_template(self.html_template, context)

    def render_content_start(self, **kwargs):
        pass

    def render_content_end(self, **kwargs):
        pass

    @abstractmethod
    def render_content_body(self, **kwargs):
        pass


    def prepare_element(self, **kwargs):
        return

    def _get_context(self, **kwargs):
        pass

    def generate_metadata(self, algorithm, **kwargs):
        pass

    def generate_context(self, algorithm, input_data, visual, **kwargs):
        pass

@define(kw_only=True)
class Container(Element):
    elements = field(factory=list)

    def create(self, **kwargs):
        """
        Create element container for output

        :param form:
        :return:
        """
        output = []

        start = self.render_content_start()
        if start:
            output.append(start)

        body = self.render_content_body(**kwargs)

        if body:
            output.append(body)

        end = self.render_content_end()

        if end:
            output.append(end)

        return "".join(output)

    def render_content_body(self, **kwargs):
        """
        For each child element renders content using the classes'
        before_add_child() the child's create function and
        the classes' after_add_child()

        :param html:
        :param form:
        :return:
        """
        child_elements = self.elements
        if child_elements is None:
            return ""

        content_list = []
        for child_element in child_elements:
            before = self.before_add_child(child_element)
            if before:
                content_list.append(before)

            content = child_element.create(**kwargs)

            if content:
                content_list.append(content)

            after = self.after_add_child(child_element)

            if after:
                content_list.append(after)

        return "".join(content_list)

    def before_add_child(self, child_element):
        """
        Rendered before each child element.

        :param child_element:
        :return:
        """
        pass

    def after_add_child(self, child_element):
        """
        Rendered after each child element.

        :param child_element:
        :return:
        """
        pass

    def generate_metadata(self, algorithm, dataset, **kwargs):
        metadata = {}
        for child_element in self.elements:
            child_metadata = child_element.generate_metadata(algorithm=algorithm, dataset=dataset, **kwargs)

            if child_metadata:
                metadata.update(child_metadata)

        return metadata

    def generate_context(self, algorithm, input_data, visual, **kwargs):
        ctx = {}
        for element in self.elements:
            element_ctx = element.generate_context(algorithm=algorithm, input_data=input_data, visual=visual, **kwargs)
            if not element_ctx:
                continue

            ctx.update(element_ctx)

        return ctx


# class InterpretElement(Element):
#     """
#     Base interpretable element for Layout
#     """
#
#     scope = None
#
#     def _new_element_block(self):
#         return HtmlBlock()
#
#     def is_correct_layout(self, layout):
#         return isinstance(layout, lo.InterpretLayout)
#
#     @classmethod
#     def is_correct_algorithm(cls, algorithm):
#         return True
#
#     html_template = None
#
#
#     def create(self, *args, **kwargs):
#         context = self._get_context(**kwargs)
#         return from_html_template(self.html_template, context)
#
#
#     def prepare_element(self, **kwargs):
#         return
#
#     def _get_context(self, **kwargs):
#         pass
#
#     def generate_metadata(self, algorithm, **kwargs):
#         pass

# InterpretInfo = namedtuple("InterpretInfo",["result","input_data","theme"])

#
# class InterpretContainer(ContainerElement):
#     # def create(self, *args, outcome, **kwargs):
#     #
#     #     if input_data and algorithm:
#     #         kwargs['result'] = algorithm.calculate(input_data)
#     #         kwargs['input_data'] = input_data
#     #         kwargs['algorithm'] = algorithm
#     #
#     #     kwargs['theme'] = theme.RedTheme()
#     #     return super().create(*args, **kwargs)
#
#     def prepare_element(self, **kwargs):
#         pass

@define(kw_only=True)
class ValueElement(Element):
    suffix:str = field(default="")
    prefix:str = field(default="")
    format:str = field(default=None)
    round_dp:int = field(default=2)
    expression:str = field(default=None)
    hide_rag_bars:bool = field(default=False)
    use_background:bool = field(default=False)
    html_width = field(default=None)
    start_range = field(default=None)
    end_range = field(default=None)
    step_size = field(default=None)
    label_side = field(default="right")

    def retrieve_value(self, result=None, **kwargs):
        return result["value"]

    def create(self, **kwargs):
        value = self.retrieve_value(**kwargs)

        if not self.hide_rag_bars and self.start_range is not None:
            swatch = TrafficLightSwatch(self.start_range, self.end_range, self.step_size)
            bg_colour = swatch.get_bg_color_for_value(value)
            fg_colour = swatch.get_fg_color_for_value(value)

            patches = ["<span class='rag-bars d-inline-block'>"] + swatch.get_html_spans(value) + ["</span>"]
        else:
            bg_colour = "transparent"
            fg_colour = "black"
            patches = []

        if self.expression:
            ld = self.expression
            cmp = compile(ld, '', 'eval')
            value = eval(cmp, {}, {"value": value})

        if self.round_dp is not None:
            num_format = "." + str(self.round_dp) + "f"
        else:
            num_format = self.format

        if num_format:
            try:
                value = format(value, num_format)
            except ValueError:
                pass

        doc = div(class_name="py-2")

        if self.title and self.label_side == "left":
            lab = label()
            lab.add_raw_string(self.title)
            doc.add(lab)

        final_value = f"{self.prefix}{value}{self.suffix}"
        value_width = self.html_width or len(final_value)

        doc.add(span(h5(final_value),style=f"border:none;width:{value_width}em;background:{bg_colour};color:{fg_colour}", class_name="d-inline-block"))

        doc.add_raw_string("&nbsp;" + "".join(patches))

        if self.help:
            doc.add(p(i(self.help), class_='small'))

        if self.title and self.label_side == "right":
            lab = label()
            lab.add_raw_string(self.title)
            doc.add(lab)

        return str(doc)

    def generate_context(self, **kwargs):
        pass

@define(kw_only=True)
class EncodedImageElement(Element):
    html_template = "encoded_image.html"
    def _get_context(self, **kwargs)->Dict:
        img = self._draw_b64_encoded_image(**kwargs)

        return {"encoded_image": img.decode(), "field": self, "label":self.title}

@define(kw_only=True)
class FigureElement(EncodedImageElement):
    width:int = field(default=3)
    height:int = field(default=3)
    font_size:int = field(default=8)

    def _new_figure(self)->"matplotlib.pyplot.Figure":
        # Figure object is created explicitly instead of through plt.figure() due to:
        # i) non-threadsafe approach that matplotlib uses for its registry of figures and persistence of WSGI
        # ii) limit of 20 figures at a time
        #
        # although a bit more cumbersome it ensures new figures are completely new and prevents drawing over existing
        # figures.

        import matplotlib.pyplot as plt
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        plt.style.use('ggplot')
        plt.rc('xtick', labelsize=14)
        plt.rc('ytick', labelsize=14)

        fig = Figure()
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_subplot()

        try:
            fig.clear()
        except ValueError:
            pass

        fig.set_size_inches(self.width, self.height)

        ax.set_xticklabels(labels=[], fontsize=self.font_size)
        ax.set_yticklabels(labels=[], fontsize=self.font_size)

        return fig

    def _new_image(self, **kwargs):
        return Utf8EncodedImage()

    def _create_figure(self, **kwargs):
        pass

    def _draw_b64_encoded_image(self, **kwargs):
        img = self._new_image(**kwargs)

        figure = self._create_figure(**kwargs)

        # figure.suptitle(self.title, fontsize=16)


        self._store_figure_to_image(figure, img)
        return img

    def _store_figure_to_image(self, figure, img):
        figure.savefig(img, format="PNG", transparent=True, bbox_inches='tight')
        return img

from colour import Color
import math
class TrafficLightSwatch:
    RED = Color("#cc3232")
    AMBER = Color("#e7b416")
    GREEN = Color("#2dc937")

    def __init__(self, start, end, step_size):
        self.start = start
        self.end = end
        self.step_size = step_size
        self.range_size = int(self.end - self.start)
        self.steps_avail = self.range_size/self.step_size
        self.patches = self._create_color_patches()


    def _create_color_patches(self):
        number = self.range_size / self.step_size
        ga_number = int(number/2)
        ar_number = int(number/2) + 1

        ga = list(self.GREEN.range_to(self.AMBER, ga_number))
        ar = list(self.AMBER.range_to(self.RED, ar_number))
        return ga + ar[1:]

    def get_step_idx_to_show(self, value):
        value = float(value)
        if value == self.end:
            return 0

        if value == self.start:
            return self.steps_avail - 1

        std_value = value + (-self.start)
        return int(math.ceil(self.steps_avail - (std_value / self.step_size))) - 1

    def get_html_spans(self, value):
        step_to_show = self.get_step_idx_to_show(value)
        return [
            f"<span style='background:{c};width:4px;border:{'solid 1px black' if step_to_show == idx else ''}'>&nbsp;</span>"
            for idx, c in enumerate(self.patches)]

    def get_bg_color_for_value(self, value)->Color:
        idx = self.get_step_idx_to_show(value)
        return self.patches[idx]

    def get_fg_color_for_value(self, value):
        bg = self.get_bg_color_for_value(value)
        return suggest_text_color_from_fill(bg.get_web())

@define(kw_only=True)
class Prediction(ValueElement):
    """
    Show prediction/result from algorithm input data
    """

    scope = ROW_SCOPE
    label_side = "left"
    as_value = field(default=False)
    show_label = field(default=True)

    def retrieve_value(self, result, **kwargs):
        if not result:
            raise VisualDataMissing(self, scope="result")

        if self.as_value:
            return result["value"]

        return f"{result['label']}"