from attr import field, define

from easul.util import get_start_step
from easul.visual.draw.flowchart import JourneyChartSettings, MermaidCLIFlowChart
from easul.visual.element import Element

@define(kw_only=True)
class JourneyMap(Element):
    route_only:bool = field(default=False, metadata={"help": "Only show map elements which are in route"})
    data_sources:bool = field(default=False, metadata={"help":"Show possible routes following current step"} )
    start_step:str = field(metadata={"help":"Start step for logic map"}, default=None)
    after_route:bool = field(default=False, metadata = {"help": "Show possible routes following current step"})
    help = "Journey map showing what step and stage journey is currently at"
    flowchart_cls = field(default=MermaidCLIFlowChart)

    def create(self, *args, steps, step, driver, **kwargs):
        route = driver.get_route()

        start_step = steps[self.start_step] if self.start_step else get_start_step(steps)
        settings = JourneyChartSettings(route_only=self.route_only,
                                        data_sources=self.data_sources,
                                        after_route=self.after_route)

        chart = self.flowchart_cls(steps=steps, start_step=start_step, route=route, settings=settings)

        return chart.generate()
