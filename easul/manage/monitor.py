import logging
import sys
import os

from easul.error import StepDataNotAvailable, InvalidStepData

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../"))

from easul.driver import Driver
from easul.step import ActionEvent
from rich.table import Table

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)

def create_journey_steps(client):
    journeys = client.get_journeys()
    journey_steps = {}
    unique_steps = {}

    for journey in journeys:
        exclude = False
        steps = client.get_steps(journey_id=journey["id"])
        if journey["complete"] is True:
            exclude = True

        temp_steps = {}
        for step in steps:
            temp_steps[step["name"]] = {"status": step["status"], "value": step["value"]}

            if not step["name"] in unique_steps:
                unique_steps[step["name"]] = True

        if not exclude:
            journey_steps[str(journey["reference"])] = {"steps": temp_steps, "complete": journey["complete"]}

    return journey_steps, unique_steps


def generate_individual(reference, client, broker, plan):
    journey = client.get_journey(reference=reference)
    journey_id = journey["id"]
    states = client.get_current_states(journey_id=journey_id)

    table = Table(expand=True)
    table.add_column("Label")
    table.add_column("Timestamp")
    table.add_column("State")

    for state_name, state_info in states.items():
        table.add_row(state_name, state_info["timestamp"], state_info["state"])

    client_steps = client.get_steps(journey_id=journey_id)

    table2 = Table(expand=True)
    table2.add_column("Name")
    table2.add_column("Status")
    table2.add_column("Status Info")
    table2.add_column("Value")
    table2.add_column("Result")

    for step in client_steps:
        table2.add_row(step['name'], step['status'], step['status_info'], step['value'], step['result'])

    return [table,
            table2,
            generate_data_table(client_steps, plan, reference, client, broker),
            generate_raw_data_table(client_steps, plan, reference, client, broker)
            ]

def generate_data_table(client_steps, plan, reference, client, broker):
    table3 = Table(expand=True)
    table3.add_column("Name")
    table3.add_column("Data")

    driver = Driver.from_reference(reference=reference, source="UHL", client=client, broker=broker)

    for step in client_steps:
        plan_step = plan.steps[step["name"]]
        LOG.info(f"Get data from {reference} for step {step['name']}")

        if hasattr(plan_step, "_retrieve_data") and plan_step.source:

            event = ActionEvent(step=step, driver=driver, previous_outcome=None)
            try:
                data = plan_step._retrieve_data(event)
            except StepDataNotAvailable as ex:
                data = {"not_available": str(ex)}
            except InvalidStepData as ex:
                data = {"invalid_data": plan_step.source.retrieve(event.driver, plan_step),
                        "ex": str(ex).replace("[", "(").replace("]", ")")}
            table3.add_row(step['name'], str(data))
        else:
            table3.add_row(step['name'], "No data")

    return table3

def generate_raw_data_table(client_steps, plan, reference, client, broker):
    table3 = Table(expand=True)
    table3.add_column("Name")
    table3.add_column("Raw data")

    driver = Driver.from_reference(reference=reference, source="UHL", client=client, broker=broker)

    for step in client_steps:
        plan_step = plan.steps[step["name"]]
        LOG.info(f"Get raw data from {reference} for step {step['name']}")

        if hasattr(plan_step, "_retrieve_data") and plan_step.source:
            event = ActionEvent(step=step, driver=driver, previous_outcome=None)
            data = plan_step.source._retrieve_raw_data(event.driver, plan_step)
            table3.add_row(step['name'], str(data))
        else:
            table3.add_row(step['name'], "No data")

    return table3

def generate_table(client):
    from rich.table import Table

    table = Table(expand=True)
    table.add_column("Idx")
    table.add_column("Reference")
    table.add_column("Complete")
    journey_steps, unique_steps = create_journey_steps(client)

    idx = 0
    for us in unique_steps.keys():
        table.add_column(us + "[" + str(idx) + "]")
        idx += 1

    idx = 0
    refs = []
    for ref, journey_info in journey_steps.items():
        row = [str(idx), str(ref), str(journey_info["complete"])]
        steps = journey_info["steps"]
        for us in unique_steps.keys():
            if us in steps:
                row.append(str(steps[us]["status"]) + " | " + str(steps[us]["value"]))
            else:
                row.append("-")

        table.add_row(*row)
        refs.append(ref)
        idx += 1

    return refs, table


import sys, tty, os, termios

full_key_mapping = {
    127: 'backspace',
    10: 'return',
    32: 'space',
    9: 'tab',
    27: 'esc',
    65: 'up',
    66: 'down',
    67: 'right',
    68: 'left'
}
minimal_mapping = {
    127: '',
    10: 'return',
    32: ' ',
    9: '    ',
    27: '',
    65: '',
    66: '',
    67: '',
    68: ''
}


class KeyPress:
    def __init__(self, console, key_mapping=minimal_mapping):
        self.key_mapping = key_mapping
        self.old_settings = termios.tcgetattr(sys.stdin)
        self.console = console
        tty.setcbreak(sys.stdin.fileno())

    def keypress(self):
        b = os.read(sys.stdin.fileno(), 3).decode()
        if len(b) == 3:
            k = ord(b[2])
        else:
            k = ord(b)

        return self.key_mapping.get(k, chr(k))

    def prompt(self, message):
        self.console.print(message)
        k = self.keypress()
        out = ""
        while k != 'return':
            self.console.print(k, end="")
            out += k
            k = self.keypress()
        self.console.print("")
        return out

    def __delete__(self, instance):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)


from rich.console import Console
from rich.prompt import Prompt

def monitor_client(engine, plan):

    console = Console()

    # kp = KeyPress(console)
    # with Live(generate_table(), screen=False, refresh_per_second=10, console=console) as live:
    refs, tab = generate_table(engine.client)
    console.print(tab)

    while (True):

        # live.update(generate_table())
        p = Prompt.ask("Option (i<idx> = individual record; t=table)")
        if p.startswith("i"):
            idx = int(p[1:])
            ref = refs[idx]
            console.print(f"Journey {ref} (idx:{idx})")
            ind_cmps = generate_individual(ref, engine.client, engine.broker, plan)
            [console.print(i) for i in ind_cmps]

        if p == "t":
            refs, tab = generate_table(engine.client)
            console.print(tab)

            # key = kp.keypress()
            #
            # if key == "space":
            #     continue
            #
            # if key == "v":
            #     live.stop()
            #
            #     idx = kp.prompt("View which journey? (enter idx)")
            #     journey_steps, unique_steps = create_journey_steps()
            #     ref = list(journey_steps.keys())[int(idx)]
            #     steps = client.get_steps(reference=ref)
            #     from pprint import pformat
            #     console.print(pformat([step for step in steps]))
            #
            #     if kp.keypress():
            #         live.start()
            #
            # if key == "d":
            #     live.stop()
            #     jidx = kp.prompt("Data for which journey (enter idx)")
            #     sidx = kp.prompt("Data for which step (enter idx)")
            #
            #     journey_steps, unique_steps = create_journey_steps()
            #     ref = list(journey_steps.keys())[int(jidx)]
            #     step_name = list(unique_steps.keys())[int(sidx)]
            #
            #     from easul.plan.build import YamlFilePlanBuilder
            #     builder = YamlFilePlanBuilder(settings._root_path + "/" + settings.plan_file)
            #     plans = builder.build_plans()
            #     steps = plans["cap"].steps
            #     step = steps.get(step_name)
            #     from easul.engine.execute import create_client, create_broker
            #     LOG.info(f"Get data from {ref} for step {step_name}")
            #     driver = Driver.from_reference(reference=ref, source="UHL", client=create_client(), broker=create_broker())
            #
            #     if hasattr(step, "_retrieve_data"):
            #         event = ActionEvent(step=step, driver=driver, previous_outcome=None)
            #         data = step._retrieve_data(event)

