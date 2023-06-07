from typing import List

from attrs import define, field

from easul.step import Step
import uuid


@define(kw_only=True)
class JourneyChartSettings:
    route_only:bool
    data_sources:bool
    after_route:bool


@define(kw_only=True)
class MermaidCLIFlowChart:
    """
    Draw Mermaid flowchart using locally installed CLI (mermaid-cli). Requires NodeJS to be installed.
    """
    steps = field(factory=list)
    start_step:Step = field()
    route:List = field(factory=list)
    settings = field()
    current_step: Step = field(default=None)


    def __attrs_post_init__(self):
        if self.current_step is None:
            if len(self.route)==0:
                self.current_step = list(self.steps.values())[0]
            else:
                self.current_step = self.steps.get(self.route[-1])

    def generate(self):
        chart = self.create_chart()
        filename = self._write_file(chart)
        return self._read_file(filename)

    def create_chart(self):
        checked = []
        chart_lines = self._generate_chart_lines(self.start_step, checked, self.settings)

        chart_lines.append(self.start_step.name + "[" + self.start_step.title + "]")

        chart_lines.append("classDef current fill:#0ae,stroke:#333,stroke-width:4px,color:white;")

        chart_lines.append("classDef journey fill:#9cf,stroke:#88d,stroke-width:2px,color:#88d;")
        chart_lines.append("classDef non_journey fill:#eee,stroke:#ccc,stroke-width:1px,color:#aaaaaa;")

        for j in self.route:
            if j == self.current_step.name:
                continue

            chart_lines.append("class " + j + " journey;")

        chart_lines.append("class " + self.current_step.name + " current;")

        return "flowchart TD\n" + "\n".join(["\t" + l for l in chart_lines])

    def _generate_chart_lines(self, step, checked, settings):
        if step.exclude_from_chart:
            return []

        lines = []

        if step.name in checked:
            return []

        checked.append(step.name)
        lines.append(step.name + "[" + step.title + "]")

        if step.name not in self.route and step != self.start_step:
            lines.append("class " + step.name + " non_journey;")

        if settings.data_sources is True:
            if step.data_sources:
                for idx, data_source in enumerate(step.data_sources):
                    lines.append(f"ds{idx}_{step.name}[({data_source})]")
                    lines.append(f"ds{idx}_{step.name}.->{step.name}")

        for reason, possible_step in step.possible_links.items():
            
            pre_arrow = "-. "
            post_arrow = ".->"
            in_route = False

            try:
                step_idx = self.route.index(step.name)
                if step_idx < len(self.route) - 1:
                    if self.route[step_idx + 1] == possible_step.name:
                        pre_arrow = "== "
                        post_arrow = "==>"

                        in_route = True

            except ValueError:
                pass

            if settings.route_only is True and in_route is False:
                continue

            lines.append(step.name + pre_arrow + "\"" + reason + "\"" + post_arrow + possible_step.name)
            lines.extend(
                self._generate_chart_lines(possible_step, checked, settings)
            )


        return lines

    def _write_file(self, mjs_chart):
        import tempfile
        import os
        mmd = tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False)
        svg = tempfile.NamedTemporaryFile(suffix=".svg", delete=False)
        svg.close()

        mmd.write(mjs_chart)
        mmd.close()

        cmd = "mmdc -i " + str(mmd.name) + " -o " + str(svg.name)
        os.system(cmd)
        return svg.name

    def _read_file(self, filename):
        with open(filename, "r") as svg_file:
            value = svg_file.read()

        return str(value)


@define(kw_only=True)
class MermaidWebFlowChart(MermaidCLIFlowChart):
    """
    Draw Mermaid flowchart using JS library obtained from a CDN. Does not require NodeJS to be installed.
    """
    def generate(self):
        chart = self.create_chart()
        chart = chart.replace("\n", "\\n")
        chart = chart.lstrip("\\n")
        chart = chart.replace("'", '"')
        uid = uuid.uuid4()

        html = f"""
            <div class="mermaid-{uid}"></div>
            <script type="module">
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10.1.0/+esm'
                const graphDefinition = \'__diagram\';
                const element = document.querySelector('.mermaid-{uid}');
                const {{ svg }} = await mermaid.render('graphDiv-{uid}', graphDefinition);
                element.innerHTML = svg;
            </script>
            """
        html = html.replace("__diagram", chart)
        return html