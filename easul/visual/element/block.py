# from collections import UserDict
# from easul.layout.element import ElementBlock, BlockContainer
#
#
#
# class Html:
#     def __init__(self):
#         self._elements = []
#
#     def start_element(self, tag, attrs, id=None):
#         attrs = [k + "=\"" + v +"\"" for k,v in attrs.items()]
#         attr_list = " ".join(attrs)
#
#         self._elements.append(f"<{tag} {attr_list}>")
#
#     def end_element(self, tag, id=None):
#         self._elements.append(f"</{tag}>")
#
#     def add_text_element(self, tag, text, attrs, id=None):
#         self.start_element(tag, attrs)
#         self._elements.append(text)
#         self.end_element(tag)
#
#     def __repr__(self):
#         return "".join(self._elements)
#
#     def append(self, element):
#         self._elements.append(element)
#
#     def add_element(self, tag, attrs):
#         attrs = [k + "=\"" + v + "\"" for k, v in attrs.items()]
#         attr_list = " ".join(attrs)
#
#         self._elements.append(f"<{tag} {attr_list} />")
#
# class HtmlBlock(ElementBlock):
#     contentCls = Html
#
# class HtmlBlockContainer(BlockContainer):
#     contentCls = Html
#
