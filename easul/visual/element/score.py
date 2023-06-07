from attr import define, field

from easul.visual.draw import style
from easul.visual.draw.theme import RedTheme

from easul.visual.element import ValueElement, Element, EncodedImageElement
from easul.algorithm import ScoreAlgorithm
from easul.visual.draw.score import InterpretedScoreImage

@define(kw_only=True)
class ScoreValue(ValueElement):
    help = "Show score from algorithm result"
    hide_rag_bars = field(default=False, init=False)
    label_side = field(default="left", init=False)

    @classmethod
    def is_correct_algorithm(cls, algorithm):
        return isinstance(algorithm, ScoreAlgorithm)

    def retrieve_value(self, result, **kwargs):
        return result["value"]

@define(kw_only=True)
class ScoreLabel(ValueElement):
    help = "Show label from algorithm result"
    hide_rag_bars = field(default=False, init=False)
    label_side = field(default="left", init=False)

    @classmethod
    def is_correct_algorithm(cls, algorithm):
        return isinstance(algorithm, ScoreAlgorithm)

    def retrieve_value(self, result, **kwargs):
        return result["label"]

@define(kw_only=True)
class FactorTable(Element):
    help = "Table showing (where possible) a more detailed breakdown than 'factor_bars' of the contributing risk factors to scores."
    html_template = "factor_table.html"
    align = field(default="L")
    theme = field(default="easul.visual.draw.theme.RedTheme")
    retrieve_specific_fn = field(default=None)

    @classmethod
    def is_correct_algorithm(cls, algorithm):
        return isinstance(algorithm, ScoreAlgorithm)

    def _get_context(self, result, **kwargs):
        from easul.util import create_package_class
        theme = create_package_class(self.theme)

        factors = {"headings":["Title","Change to score","Reason for penalty"],"data": style.get_styled_factors([
            {"text": f["title"], "penalty": "+" + str(f["penalty"]) if f["penalty"] > 0 else str(f["penalty"]), "expression":f["expression"]}
            for f in result["matched_factors"]], theme)
        }

        return {"factors": factors, "field":self, "title":self.title, "align":self.align}

@define(kw_only=True)
class FactorBars(EncodedImageElement):
    help = "Bar plot showing the contribution of different factors to the score"
    single_block_width:int = field(default=None)
    width:int = field(default=1000)
    height:int = field(default=500)
    theme = field(default=RedTheme)

    @classmethod
    def is_correct_algorithm(cls, algorithm):
        return isinstance(algorithm, ScoreAlgorithm)

    def _draw_b64_encoded_image(self, *args, result, **kwargs):
        theme = self.theme

        if self.single_block_width:
            theme.single_block_width = self.single_block_width

        inter = InterpretedScoreImage(theme, self.width, self.height)
        return inter.create_encoded_image(result)