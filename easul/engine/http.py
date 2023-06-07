import requests
from easul.engine import Client, ClientError
from easul.engine.codec import JsonCodec, NpDecoder
from urllib3.exceptions import MaxRetryError
from requests.exceptions import ConnectionError

import itertools
import logging
import time

LOG = logging.getLogger(__name__)

class HttpApi:
    """
    HTTP-API
    """
    def __init__(self, base_url, token=None, username=None, password=None, retry=True, secs_to_retry=10):
        self._base_url = base_url
        self._token = token
        self._retry = retry
        self._secs_to_retry = secs_to_retry

        self._session = requests.Session()
        self._session.headers["Content-type"] = "application/json"

        if username and password:
            self._session.auth = (username, password)

    def _make_request(self, method, url_path, **kwargs):
        request_path = self._base_url + "/" + url_path + "/"

        try:
            resp = getattr(self._session, method)(url = request_path, **kwargs)
            json = self._extract_response_json(resp)

            return json
        except ConnectionError:
            if self._retry is True:
                LOG.warning(f"Unable to connect to client ({self._base_url}) - retrying in {self._secs_to_retry}s")
                time.sleep(self._secs_to_retry)
                return self._make_request(method, url_path, **kwargs)
            else:
                raise ClientError(request_path, kwargs, None)
        except MaxRetryError:
            raise ClientError(request_path, kwargs, None)

    def get_json_request(self, url_path, params=None, **kwargs):
        if not params:
            params = {}

        return self._make_request("get", url_path, params=params, headers=self.headers, **kwargs)

    @property
    def headers(self):
        return {"Content-Type":"application/json"}
        #"Authorization": "Token " + self._token, "Content-type":"application/json"}

    def post_json_request(self, url_path, params=None, data=None, **kwargs):
        if not params:
            params = {}
        params.update()

        encoded = JsonCodec.encode(data)

        return self._make_request("post", url_path, data=encoded, headers=self.headers)

    def _extract_response_json(self, response):
        if response.status_code<200 or response.status_code>=300:
            raise ClientError(url=response.url, data=response.content, status_code=response.status_code)

        return response.json()

    def put_json_request(self, url_path, params=None, data=None, **kwargs):
        if not params:
            params = {}
        params.update()

        encoded = JsonCodec.encode(data)
        return self._make_request("put", url_path, data=encoded, headers=self.headers)


    def create_or_update_single(self, url_path, search_params, data, update_existing=False):

        try:
            existing = self.retrieve_single_item(url_path, params=search_params)
            if update_existing is False and existing:
                return existing
        except LookupError:
            return self.post_json_request(url_path, data=data)

        return self.put_json_request(url_path + "/" + str(existing['id']), data=data)

    def retrieve_single_item(self, url_path, id=None, params=None):
        if id:
            url_path += "/" + str(id)

        items = self._make_request("get", url_path, params=params)

        if type(items) is dict:
            return items

        if len(items)==0:
            raise LookupError(f"No {url_path} matching {params}")

        if len(items)>1:
            raise ValueError(f"Multiple {url_path} matching {params}")

        return items[0]

    def __repr__(self):
        return f"<HttpApi base_url={self._base_url}>"

class HttpClient(Client):
    """
    HTTP-based client which wraps HTTP-API
    """
    def __init__(self, api_cls=HttpApi, **kwargs):
        self._api = api_cls(**kwargs)


    def __repr__(self):
        return f"<HttpClient api={self._api}>"

    def create_journey(self, reference, source, label=None):
        return self._api.create_or_update_single("journeys",{"reference":reference},{"reference":reference, "source":source, "label":label})

    def retrieve_journey(self, reference_id):
        try:
            journey = self._api.retrieve_single_item("journeys", params={"reference":reference_id})
            return journey
        except LookupError:
            return None

    def get_journey(self, id=None, reference=None, source=None):
        if (not id) and (not reference):
            raise AttributeError("Must provide journey_id OR reference and source")

        try:
            if id:
                journey = self._api.retrieve_single_item("journeys", id = id)
            else:
                journey = self._api.retrieve_single_item("journeys", params={"reference":reference, "source":source})
        except LookupError:
            return None

        return journey

    def set_current_state(self, state_label, state, journey_id=None, reference=None, reason=None, from_step=None, timestamp=None):
        if reference:
            journey = self.retrieve_journey(reference)
            journey_id = journey['id']

        states = self._api.get_json_request("states",params={"journey":journey_id, "label":state_label})

        if len(states)>0:
            current_state = states[-1]["state"]

            if current_state == state:
                LOG.debug(f"Set state '{current_state}' is same as current state")
                return None

        return self._api.post_json_request("states", data={"journey":journey_id, "label":state_label,"state":state, "reason":reason, "from_step":from_step})

    def set_current_step(self, step_name, status, status_info=None, journey_id=None, reference=None, outcome=None, timestamp=None):
        if reference:
            journey = self.retrieve_journey(reference)
            journey_id = journey['id']

        steps = self._api.get_json_request("steps", params={"journey": journey_id, "name":step_name})

        data = {
            "journey": journey_id,
            "name": step_name,
            "status": status,
            "outcome":outcome,
            "result":outcome.get("result") if outcome else None,
            "context": outcome.get("context") if outcome else None,
            "value":str(outcome.get("result",{}).get("value")) if outcome else None
        }

        if len(steps) > 0:
            c_step = steps[-1]
            c_status = c_step["status"]
            c_id = c_step["id"]

            if c_status == status:
                if status!="READY":
                    return None

            return self._api.put_json_request("steps/" + str(c_id), data=data)

        return self._api.post_json_request("steps", data=data)


    def mark_complete(self, reference):
        journey = self.retrieve_journey(reference_id=reference)
        return self._api.put_json_request("journeys/" + str(journey["id"]), data={"reference":reference, "complete":1})

    def get_current_state(self, state_label, journey_id=None, reference=None):
        if reference:
            journey = self.retrieve_journey(reference)
            journey_id = journey['id']


        states = self._api.get_json_request("states",params={"journey":journey_id, "label":state_label})
        return states[-1]["state"]

    def get_current_states(self, journey_id=None, reference=None):
        if reference:
            journey = self.retrieve_journey(reference)
            journey_id = journey['id']

        states = self._get_json_request("states", params={"journey": journey_id})

        states_by_label = itertools.groupby(states, lambda x:x["label"])

        current_states = {}

        for label, states in states_by_label:
            sorted_states = sorted(states, key=lambda x:x["timestamp"], reverse=True)
            current_states[label] = sorted_states[0]

        return current_states

    def get_all_states(self, journey_id=None, reference=None):
        if reference:
            journey = self.retrieve_journey(reference)
            journey_id = journey['id']

        return self._api.get_json_request("states", params={"journey": journey_id})

    def get_latest_step(self, journey_id=None, reference=None):
        if reference:
            journey = self.retrieve_journey(reference)
            journey_id = journey['id']

        steps = self._api.get_json_request("steps", params={"journey": journey_id})

        if len(steps) == 0:
            return None

        return steps[-1]

    def get_step_route(self, journey_id):
        steps = self._api.get_json_request("steps", params={"journey": journey_id})


        route = []

        steps = sorted(steps, key=lambda x: x["timestamp"])

        for step in steps:
            if step["name"] in route:
                continue

            route.append(step["name"])

        return route

    def get_step(self, step_name, journey_id=None, reference=None):
        if reference:
            journey = self.retrieve_journey(reference)
            journey_id = journey['id']

        steps = self._api.get_json_request("steps", params={"journey": journey_id, "name":step_name})

        if len(steps) == 0:
            return None

        step = steps[-1]

        return step