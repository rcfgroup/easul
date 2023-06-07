import itertools

import requests

from easul.engine import Client, ClientError
from easul.outcome import FailedOutcome

import logging
LOG = logging.getLogger(__name__)
import time


class LocalApi:
    def retrieve_get_data(self, url_path, url_params):
        from django.http import HttpRequest
        from django.urls import resolve

        request = HttpRequest()
        request.method = "GET"
        request.META["PATH_INFO"] = url_path
        request.GET.update(url_params)
        request.META["CONTENT_TYPE"] = "application/json"

        view_set = resolve(url_path)
        if not view_set:
            raise SystemError(f"Path '{url_path}' does not resolve to a view")

        resp = view_set.func(request)

        if resp:
            return resp.render().dataset

        return []

    def retrieve_single_item(self, url_path, id=None, params=None):
        if id:
            url_path = url_path + "/" + str(id)
            params = {}

        data = self.retrieve_get_data("/" + url_path + "/", params)

        return data[0]

    def get_json_request(self, url_path, params=None, **kwargs):
        if not params:
            params = {}

        from urllib3.exceptions import MaxRetryError

        try:
            resp = self._session.get(url = self._base_url + "/" + url_path, params=params, headers=self.headers, **kwargs)
            return self._extract_response_json(resp)
        except ConnectionError:
            raise ClientError(self._base_url + "/" + url_path, params, None)
        except MaxRetryError:
            raise ClientError(self._base_url + "/" + url_path, params, None)

class HttpApi:
    def __init__(self, base_url, token=None, username=None, password=None, retry=True, secs_to_retry=10):
        self._base_url = base_url
        self._token = token
        self._reattempt = reattempt
        self._timeout = timeout
        self._secs_to_retry = secs_to_retry

        self._session = requests.Session()
        self._session.headers["Content-type"] = "application/json"

        if username and password:
            self._session.auth = (username, password)

        LOG.debug(f"API client init [base_url:{base_url}]")

    def _make_request(self, method, url_path, **kwargs):
        LOG.debug(f"API item {method} [{kwargs}]")

        try:
            resp = getattr(self._session, method)(url = self._base_url + "/" + url_path, **kwargs)
            return self._extract_response_json(resp)
        except ConnectionError:
            if self._reattempt is True:
                LOG.warning(f"Unable to connect - retrying in {self._secs_to_retry}")
                time.sleep(self._secs_to_retry)
                return get_json_request(url_path, params, **kwargs)
            else:
                raise ClientError(self._base_url + "/" + url_path, params, None)
        except MaxRetryError:
            raise ClientError(self._base_url + "/" + url_path, params, None)

    def get_json_request(self, url_path, params=None, **kwargs):
        if not params:
            params = {}

        from urllib3.exceptions import MaxRetryError

        return self._make_request("get",self._base_url + "/" + url_path, params=params, headers=self.headers, **kwargs)

    @property
    def headers(self):
        return {}
        #"Authorization": "Token " + self._token, "Content-type":"application/json"}

    def post_json_request(self, url_path, params=None, data=None, **kwargs):
        if not params:
            params = {}
        params.update()

        return self._make_request("post", self._base_url + "/" + url_path + "/", json=data, headers=self.headers)


    def patch_json_request(self, url_path, params=None, data=None, **kwargs):
        if not params:
            params = {}

        params.update()

        return self._make_request("patch",self._base_url + "/" + url_path + "/", json=data, headers=self.headers)

    def _extract_response_json(self, response):
        try:
            if response.status_code < 200 or response.status_code >= 300:
                raise ClientError(url=response.url, data=response.content, status_code=response.status_code)

            return response.json()
        except ConnectionError:
            if self._reattempt is True:
                LOG.warning(f"Unable to connect - retrying in {self._secs_to_retry}")
                time.sleep(self._secs_to_retry)
                return get_json_request(url_path, params, **kwargs)
            else:
                raise ClientError(self._base_url + "/" + url_path, params, None)
        except MaxRetryError:
            raise ClientError(self._base_url + "/" + url_path, params, None)


    def put_json_request(self, url_path, params=None, data=None, **kwargs):
        if not params:
            params = {}
        params.update()

        return self._make_request("put", self._base_url + "/" + url_path + "/", json=data, headers=self.headers)


    def retrieve_single_item(self, url_path, id=None, params=None):
        if id:
            url_path += "/" + str(id) + "/"

        items = self.get_json_request(url_path, params=params)

        LOG.info(f"API item retrieved [url_path:{url_path}, items:{items}]")

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
    def __init__(self, api_cls=HttpApi, **kwargs):
        self._api = api_cls(**kwargs)


    def __repr__(self):
        return f"<HttpClient api={self._api}>"

    def create_journey(self, reference, source, label=None, update_existing=False):
        url_path = "journeys"
        try:
            LOG.debug(f"Create journey [reference:{reference}]")
            existing = self._api.retrieve_single_item("journeys", params={"reference":reference})
            if update_existing is False and existing:
                LOG.debug(f"Client existing journey found and not updated [reference:{reference}, id:{existing['id']}]")
                return existing

            fn = self._api.put_json_request
            url_path = "journeys/" + str(existing['id']) + "/"
        except LookupError:
            fn = self._api.post_json_request

        return fn(url_path,data={"reference":reference, "source":source, "label":label})

    def retrieve_journey(self, reference_id):
        try:
            journey = self._api.retrieve_single_item("journeys", params={"reference":reference_id})
            return journey
        except LookupError:
            return None

    def complete_journey(self, journey_id=None, reference=None):
        try:
            if not journey_id:
                existing = self.retrieve_journey(reference_id=reference)
                journey_id = existing["id"]
            self._api.patch_json_request("journeys/" + str(journey_id),data={"complete":1})
        except LookupError:
            raise ClientError(f"Cannot complete journey '{journey_id}'")

    def get_journey(self, id=None, reference=None, source=None):
        if (not id) and not (reference and source):
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

        if timestamp:
            states = self._api.get_json_request("states", params={"journey": journey_id, "label": state_label, "timestamp":timestamp})
        else:
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

        if outcome and not issubclass(outcome.__class__, FailedOutcome):
            result = outcome.get("result")
            value = outcome.get("result",{}).get("value")
        else:
            result = None
            value = None

        data = {"journey": journey_id, "name": step_name, "status": status, "status_info":str(status_info) if status_info else "", "outcome":outcome, "result":result if outcome else None, "value":value, "timestamp":timestamp}

        if len(steps) > 0:
            c_step = steps[-1]
            c_status = c_step["status"]
            c_id = c_step["id"]

            if c_status == status:
                if status!="READY":
                    return None

            return self._api.put_json_request("steps/" + str(c_id) + "/", data=data)

        return self._api.post_json_request("steps", data=data)


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
        step = self._api.retrieve_single_item("steps",params={"journey":journey_id,"name":step_name})
        return step

class LocalClient(HttpClient):
    def __init__(self, api_cls=LocalApi, **kwargs):
        self._api = api_cls(**kwargs)

    def __repr__(self):
        return f"<LocalApi>"
