from typing import List

from attr import field, define, validators
from easul.visual.element import Element, Html


@define(kw_only=True)
class BulletPoints(Element):
    help = "Unordered bulletpointed list for title or emphasis."
    items:List[str] = field(factory=list, metadata={"help":"List of items as string"})

    def create(self, *args, **kwargs):
        html = Html()
        html.start_element("ul")
        for bp in self.items:
            html.add_text_element("li",bp)
        html.end_element("ul")

        return str(html)


class Message(Element):
    help = "Message display"

    def create(self, *args, **kwargs):
        return f"<div class='alert alert-success'>{self.title}</div>"

@define(kw_only=True)
class Heading(Element):
    help = "HTML heading display"
    heading_level:int = field(validator=validators.and_(validators.ge(1),validators.le(6)), metadata={"help":"HTML heading level from 1-6"})

    def create(self, *args, **kwargs):
        return f"<h{self.heading_level}>{self.title}</h{self.heading_level}>"
