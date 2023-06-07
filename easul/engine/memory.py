import datetime as dt
import itertools

from easul.engine import Client, Broker, Channels
from easul.util import is_successful_outcome
import logging

LOG= logging.getLogger(__name__)

class MemoryClient(Client):
    """
    Client which persist all information in internal data structures.
    """
    def __init__(self):
        self._journeys = {}
        self._journey_idx = {}
        self._steps = {}
        self._states = {}

    def complete_journey(self, journey_id=None, reference=None):
        if not reference in self._journeys:
            raise ValueError(f"Journey does not exist [journey_id:{journey_id}, reference:{reference}]")

        self._journeys[reference]["complete"]=1

    def create_journey(self, reference, source, label=None):
        curr_journey_id = len(self._journey_idx)
        journey = {"id":curr_journey_id, "reference":reference, "source":source, "label":label, "states":[], "steps":[]}
        self._journeys[reference] = journey
        self._journey_idx[curr_journey_id] = reference
        return journey

    def retrieve_journey(self, reference_id):
        return self._journeys.get(reference_id)

    def get_journey(self, id=None, reference=None, source=None):
        if not reference:
            reference = self._journey_idx[id]

        if reference not in self._journeys:
            return None

        return self.retrieve_journey(reference)

    def get_journeys(self):
        return list(self._journeys.values())

    def set_current_state(self, state_label, state, journey_id=None, reference=None, reason=None, from_step=None, timestamp=None):
        journey = self.get_journey(id = journey_id, reference=reference)
        self._journeys[journey["reference"]]["states"].append({"label":state_label, "status":state, "timestamp":timestamp})

    def set_current_step(self, step_name, status, status_info=None, journey_id=None, reference=None, outcome=None, timestamp=None):
        journey = self.get_journey(id=journey_id, reference=reference)

        steps = self._journeys[journey["reference"]]["steps"]

        for sidx, step in enumerate(steps):
            if step.get("name") == step_name and step.get("timestamp") == timestamp:
                steps[sidx].update({
                    "status":status,
                    "timestamp":timestamp,
                    "status_info":status_info,
                    "outcome":outcome,"result":outcome.get("result") if is_successful_outcome(outcome) else None,
                    "next_step":outcome.get("next_step") if is_successful_outcome(outcome) else None,
                    "value":outcome.get("result",{}).get("value") if is_successful_outcome(outcome) else None
                })
                return

        self._journeys[journey["reference"]]["steps"].append({"name":step_name,"status":status,"next_step":outcome.get("next_step") if outcome else None, "outcome":outcome, "timestamp":timestamp,"status_info":status_info,"result":outcome.get("result") if is_successful_outcome(outcome) else None, "value":outcome.get("result",{}).get("value") if is_successful_outcome(outcome) else None})


    def get_current_state(self, state_label, journey_id=None, reference=None, timestamp=None):
        journey = self.get_journey(id=journey_id, reference=reference)

        for state in self._journeys[journey["reference"]]["states"]:
            if state.get("label") == state_label:
                return state

        return None

    def get_current_states(self, journey_id=None, reference=None):
        all_states = self.get_all_states(journey_id=journey_id, reference=reference)
        states_by_label = itertools.groupby(all_states, lambda x: x["label"])

        current_states = {}

        for label, states in states_by_label:
            sorted_states = sorted(states, key=lambda x: x["timestamp"] if x["timestamp"] else dt.datetime.min, reverse=True)
            current_states[label] = sorted_states[0]

        return current_states

    def get_all_states(self, journey_id=None, reference=None):
        journey = self.get_journey(id=journey_id, reference=reference)
        return self._journeys[journey["reference"]]["states"]

    def get_latest_step(self, journey_id=None, reference=None):
        journey = self.get_journey(id=journey_id, reference=reference)

        steps = self._journeys[journey["reference"]]["steps"]

        if len(steps)>0:
            return steps[-1]

        return None

    def get_step(self, step_name, journey_id=None, reference=None):
        journey = self.get_journey(id=journey_id, reference=reference)

        steps = self._journeys[journey["reference"]]["steps"]

        match_steps = list(filter(lambda x: x["name"] == step_name, steps))

        if len(match_steps)==0:
            return None

        sorted_steps = sorted(match_steps, key=lambda x:x["timestamp"], reverse=True)
        return sorted_steps[0]

    def get_step_route(self, journey_id):
        journey = self.get_journey(id=journey_id)

        steps = self._journeys[journey["reference"]]["steps"]


        route = []

        steps = sorted(steps, key=lambda x: x["timestamp"] or dt.datetime.min)

        for step in steps:
            if step["name"] in route:
                continue

            route.append(step["name"])

        return route

class MemoryBroker(Broker):
    """
    Broker which persists all information in internal data structure.
    """
    def __init__(self):
        self._store = {}
        self._messages = {Channels.EXTERNAL:[], Channels.INTERNAL:[]}

    def store_data(self, reference, data_type, data, external=False, send_message=True):
        if data_type not in self._store:
            self._store[data_type] = {}

        self._store[data_type][reference] = data

        if send_message:
            if external:
                self._messages[Channels.EXTERNAL].append({"reference":reference, "data_type":data_type, "data":data})
            else:
                self._messages[Channels.INTERNAL].append({"reference":reference})

    def retrieve_data(self, reference, data_type):
        if data_type not in self._store:
            return None

        return self._store[data_type].get(reference)

    def send_message(self, channel_name, data):
        self._messages[channel_name].append(data)