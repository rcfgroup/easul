from attr import field, define

from easul.visual.element import Container, Html
from attr import define, field

@define(kw_only=True)
class VerticalContainer(Container):
    show_label = field(default=False)
    def render_content_start(self):
        html = Html()
        name = self.name
        attrs = {
            "id": name,
            "name": name,
            "style": self.style,
            "class": "vcontainer " + self.html_class
        }

        html.start_element("div", attrs)

        if self.title and self.show_label:
            html.add_text_element("label", self.title,{"style":"font-weight:bold"})

        return str(html)

    def render_content_end(self):
        return "</div>"

    def prepare_element(self, **kwargs):
        pass


    def before_add_child(self, child_field):
        return "<div class=\"py-2\">"

    def after_add_child(self, child_field):
        return "</div>"

@define(kw_only=True)
class CardContainer(Container):
    heading_level = field(default=5)

    def render_content_start(self):
        html = Html()
        name = self.name
        attrs = {
            "id": name,
            "name": name,
            "style": self.style,
            "class": "card " + self.html_class + "my-3"
        }

        html.start_element("div", attrs)

        if self.title:
            html.start_element("div",{"class":"card-header"})
            html.add_text_element(f"h{self.heading_level}", self.title,{"class":"card-title"})
            html.end_element("div")

        html.start_element("div",{"class":"card-body"})
        return str(html)


    def before_add_child(self, child_field):
        return "<div class=\"py-2\">"

    def after_add_child(self, child_field):
        return "</div>"

    def render_content_end(self):
        return "</div></div>"

    def prepare_element(self, **kwargs):
        pass

@define(kw_only=True)
class HorizContainer(Container):
    segments = field(default=None)
    show_label = field(default=False)

    """
    Horizontal container which will layout fields horizontally next to each
    other, or if a 'segments' setting is provided, a certain number of equal
    sized areas.

    The 'style' setting will be append to container start CSS. The class
    type contains 'horiz-container'
    """

    @property
    def main_class_name(self):
        if self.segments:
            return "row"
        else:
            return "row"

    def render_content_start(self):
        html = Html()
        name = self.name
        attrs = {
            "id": name,
            "name": name,
            "style": self.style,
            "class": self.main_class_name + " hcontainer " + self.html_class
        }

        html.start_element("div", attrs)

        if self.title and self.show_label:
            html.add_text_element("label", self.title,{"style":"font-weight:bold"})

        return str(html)

    def before_add_child(self, child_field):
        if self.segments:
            segment = int(self.segments)
            col_num = int(12/segment)
            html_class = "col-sm-auto px-3 pb-3" if child_field.fill_container else f"col-sm-" + str(col_num)
        else:
            html_class = "col" if child_field.fill_container else "col-sm-auto px-3 pb-3"

        return f"<div class=\"{html_class}\">"

    def after_add_child(self, child_field):
        return "</div>"

    def render_content_end(self):
        return "</div>"
