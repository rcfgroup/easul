from jinja2 import loaders
from jinja2.environment import Environment

import matplotlib

import easul as cm
import logging
LOG = logging.getLogger(__name__)

env = Environment(loader=loaders.ChoiceLoader([loaders.PackageLoader("easul","templates")]))

def from_html_template(template_file, context):
    return env.get_template(template_file).render(**context)


class PlainRenderer:
    def setup_render(self):
        matplotlib.use('Agg')
        return [
            """
                <style>label.easul { font-weight:bold; display:block; }



                </style>
            """
        ]

    def render(self, data):
        pass

    def create(self, visual, **kwargs):
        rendered = self.setup_render()


        for element in visual.elements:
            html = element.create(**kwargs, visual=visual)
            rendered.append(html)

        final_list = list(map(str, rendered))
        data = "".join(final_list)
        self.render("".join(final_list))
        return data

class JupyterRenderer(PlainRenderer):
    def setup_render(self):
        matplotlib.use('nbAgg')
        return [
            """
                <style>label.easul { font-weight:bold; display:block; }
                </style>
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"/>
            """
        ]

    def render(self, data):
        from IPython.display import HTML, display_html

        display_html(HTML(data))

    def create(self, visual, **kwargs):
        super().create(visual, **kwargs)

