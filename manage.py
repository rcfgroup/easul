#!/usr/bin/env python
import typer
import logging
import os

# logging.basicConfig(level=logging.INFO, format="%(asctime)s %(filename)s: %(levelname)6s %(message)s")
#
# LOG = logging.getLogger(__name__)

from easul.driver import MemoryDriver

app = typer.Typer(help="EASUL tools to manage and extend the abilities of the library. Most of the tools are related to the running and monitoring the engine.", pretty_exceptions_enable=False)

@app.command(help="View visuals for a specific step")
def view_visual(plan_module, stepname:str):
    from easul.util import create_package_class
    plan = create_package_class(plan_module)
    step = plan.steps[stepname]

    driver = MemoryDriver.from_reference("VISUAL")
    html = step.render_visual(driver, plan.steps)

    import tempfile

    fd = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
    fd.write(str(html).encode("utf8"))
    fd.close()
    os.system(f"open {fd.name}")

@app.command(help="Regenerate model algorithm and context data for EASUL tests.", epilog="NOTE: Only use this if files are lost or corrupted - it may require changes to tests.")
def regenerate_test_models():
    from easul.manage.regenerate import generate_test_models
    generate_test_models()

@app.command(help="Run EASUL engine according to provided configuration")
def run_engine(plan_module:str, engine_module:str):
    from easul.util import create_package_class
    plan = create_package_class(plan_module)()
    engine = create_package_class(engine_module)()

    engine.run(plan)

@app.command(help="Monitor EASUL broker for supplied plan/engine")
def monitor_broker(plan_module:str, engine_module:str):
    from easul.util import create_package_class
    plan = create_package_class(plan_module)()
    engine = create_package_class(engine_module)()

    from easul.manage.monitor import monitor_client
    monitor_client(engine, plan)

if __name__ == "__main__":
    app()

