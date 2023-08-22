
def visualise_plan(plan, start_step=None, use_external=False, renderer=None):
    """
    Helper function for visualising plans in Jupyter notebooks
    Args:
        plan:
        start_step:
        use_external:
        renderer:

    Returns:

    """
    from easul.visual import Visual
    from easul.visual.element.journey import JourneyMap
    from easul.visual.draw.flowchart import MermaidWebFlowChart, MermaidCLIFlowChart


    fc_cls = MermaidWebFlowChart if use_external is True else MermaidCLIFlowChart

    v = Visual(
            elements=[
                JourneyMap(route_only=False, after_route=True, data_sources=True, start_step=start_step, flowchart_cls=fc_cls)
            ])
    from easul.driver import Clock, EmptyDriver

    driver = EmptyDriver(client=None, broker=None, clock=Clock())

    if not renderer:
        from easul.visual.render import JupyterRenderer

        renderer = JupyterRenderer()

    v.render(driver=driver, steps=plan.steps, renderer=renderer)


def simulate_run(plan, input_data):
    """
    Helper function for simulating runs in Jupyter notebooks.
    Args:
        plan:
        **input_data:

    Returns:

    """
    driver, plan_copy =_simulate_driver_run(plan, input_data)
    return driver.journey["steps"], driver.journey["states"]

def copy_plan_with_constant_data(plan, input_data):
    from easul.util import copy_plan_with_new_sources, NamedDict
    from easul.source import ConstantSource

    new_sources = NamedDict()

    for name, source_data in input_data.items():
        original_source = plan.sources.get(name)

        new_sources[name] = ConstantSource(title=original_source.title, processes=original_source.processes,
                                         data=source_data)

    return copy_plan_with_new_sources(plan, new_sources)

def _simulate_driver_run(plan, input_data):
    from easul.driver import MemoryDriver, LocalClock
    driver = MemoryDriver.from_reference(reference="SIMULATE", autocreate=True, clock=LocalClock())

    plan_copy = copy_plan_with_constant_data(plan, input_data)

    plan_copy.run(driver)

    return driver, plan_copy

def visualise_run(plan, input_data, use_external=False, renderer=None):
    """
    Helper function to enable visualisation of patient journey/run in Jupyter notebooks allowing particular data to
    be provided to drive the process.
    Args:
        plan:
        input_data:
        use_external:
        renderer:

    Returns:

    """
    from easul.visual.draw.flowchart import MermaidWebFlowChart, MermaidCLIFlowChart

    driver, plan_copy = _simulate_driver_run(plan, input_data)

    from easul import Visual
    from easul import JourneyMap

    if not renderer:
        from easul.visual.render import JupyterRenderer

        renderer = JupyterRenderer()

    fc_cls = MermaidWebFlowChart if use_external is True else MermaidCLIFlowChart

    v = Visual(
        elements=[
            JourneyMap(route_only=False, after_route=True, data_sources=True, flowchart_cls=fc_cls)
        ])

    v.render(driver=driver, steps=plan.steps, renderer=renderer)

def visualise_step(step_name, plan, input_data, renderer=None):
    """
    Helper function to show visuals from particular steps in Jupyter notebooks based on supplied input data.
    Args:
        step_name:
        plan:
        input_data:
        renderer:

    Returns:

    """
    if not renderer:
        from easul.visual.render import JupyterRenderer

        renderer = JupyterRenderer()

    driver, plan_copy = _simulate_driver_run(plan, input_data)
    step = plan_copy.steps.get(step_name)

    if not step:
        raise ValueError(f"Step '{step_name}' does not exist in plan")

    return step.render_visual(driver=driver, steps=plan.steps, renderer=renderer)

def describe_step(step_name, plan, renderer=None):
    """
    Helper function to describe components of step as rendered table in Jupyter notebooks
    Args:
        step_name:
        plan:
        renderer:

    Returns:

    """
    if not renderer:
        from easul.visual.render import JupyterRenderer
        renderer = JupyterRenderer()

    step = plan.steps.get(step_name)

    if not step:
        raise ValueError(f"Step '{step_name}' does not exist in plan")

    return renderer.render(_create_table(step.describe()))


def describe_plan(plan, renderer=None):
    """
    Helper function to describe steps in plan as a rendered table in Jupyter notebooks
    Args:
        plan:
        renderer:

    Returns:

    """
    if not renderer:
        from easul.visual.render import JupyterRenderer
        renderer = JupyterRenderer()

    def has_property(step, prop_name):
        tick = "<i class='fas fa-check'>"
        no_tick = "&nbsp;"

        if not hasattr(step, prop_name):
            return no_tick

        return tick if getattr(step, prop_name) else no_tick

    html = ["<table>"]
    html.append("<tr>")
    html.extend([f"<th>{c}</th>" for c in ["step","title","has visual?","has source?", "has algorithm?","has decision?"]])
    html.append("</tr>")

    for k,v in plan.steps.items():
        html.append("<tr>")
        row = [k,
       v.title,
       has_property(v, "visual"),
        has_property(v, "source"),
        has_property(v, "algorithm"),
        has_property(v, "decision")]
        html.extend([f"<td>{c}</td>" for c in row])
        html.append("</tr>")

    html.append("</table>")
    return renderer.render("".join(html))

def _create_table(data):
    if isinstance(data, dict):
        return "<table>" + "".join([f"<tr><td>{k}</td><td>{_create_table(v)}</td></tr>" for k,v in data.items()]) + "</table>"
    if isinstance(data, list):
        return "<table>" + "".join([f"<tr><td>{_create_table(v)}</td></tr>" for v in data]) + "</table>"

    return str(data)

def simulate_decision(step_name, plan, input_data, renderer=None, as_data=False):
    """
    Helper function to simulate a journey based on specific input data and obtain a decision for a specific step
    either as an rendered table or as a Python dictionary (as_data=True)

    Args:
        step_name:
        plan:
        input_data:
        renderer:

    Returns:

    """
    if not renderer:
        from easul.visual.render import JupyterRenderer
        renderer = JupyterRenderer()

    driver, plan_copy = _simulate_driver_run(plan, input_data)
    step = driver.get_specific_step(step_name)
    if not step:
        raise ValueError(f"Step '{step_name}' has no outcome")

    outcome = step.get("outcome")
    del outcome["context"]
    del outcome["input_data"]

    if as_data is True:
        return outcome

    return renderer.render(_create_table(outcome))
