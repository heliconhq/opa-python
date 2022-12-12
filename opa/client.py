import typing
import json

import requests

from urllib import parse
from requests.adapters import HTTPAdapter, Retry

from .exceptions import (
    Unauthorized,
    InvalidURL,
    ConnectionError,
    InvalidPolicy,
    InvalidPolicyRequest,
    PolicyRequestError,
    PolicyNotFound,
    DocumentNotFound,
)

Explain = typing.Literal["notes", "fails", "full", "debug"]


class OPAClient:
    timeout = 15000

    def __init__(self,
                 url: str = "localhost",
                 verify: bool = True,
                 token: typing.Optional[str] = None):
        self.url = self.parse_url(url)
        self.verify = verify
        self.token = token

    def parse_url(self, url: str) -> str:
        """Parse and perform basic validation of supplied `url`."""
        try:
            o = parse.urlparse(url)
        except AttributeError:
            raise InvalidURL("Invalid URL type.")

        if not o.scheme:
            o = parse.urlparse(f'http://{url}')

        if not o.hostname:
            raise InvalidURL("Malformed URL. Missing hostname.")

        if o.scheme not in ['http', 'https']:
            raise InvalidURL(f"Invalid scheme '{o.scheme}'.")

        return parse.urlunparse([o.scheme, o.netloc, o.path, None, None, None])

    def package_path(self, package):
        return package.replace(".", "/").lstrip("/")

    def request(self, verb, path, *args, **kwargs) -> requests.Response:
        """Make a request to OPA server."""

        headers = {}
        if self.token is not None:
            headers["Authorization"] = f"Bearer {self.token}"

        url = parse.urljoin(self.url, path)

        try:
            updated_kwargs = dict(
                kwargs,
                headers=headers,
                timeout=self.timeout,
                verify=self.verify,
            )
            resp = requests.request(verb, url, **updated_kwargs)

            if resp.status_code == 401:
                raise Unauthorized(resp.json())

            return resp
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Unable to connect to OPA server.")

    # check_permission
    # check_policy_rule

    def check_health(self) -> None:
        with requests.Session() as s:
            headers = {}
            if self.token is not None:
                headers["Authorization"] = f"Bearer {self.token}"

            url = parse.urljoin(self.url, '/health')

            retries = Retry(total=10, backoff_factor=0.2)
            s.mount(url, HTTPAdapter(max_retries=retries))

            try:
                resp = s.get(url, headers=headers)
            except requests.exceptions.ConnectionError:
                raise ConnectionError("Unable to connect to OPA server.")

            if resp.ok:
                return resp.json()

            if resp.status_code == 401:
                raise Unauthorized(resp.json())

            raise ConnectionError("Connection not healthy.")

    # Data API

    def check_policy(self,
                     input: dict,
                     package: str,
                     raw: bool = False,
                     pretty: bool = False,
                     provenance: bool = False,
                     instrument: bool = False,
                     strict: bool = False,
                     explain: typing.Optional[Explain] = None,
                     metrics: bool = False) -> dict:
        """Get decision for a named policy."""
        path = parse.urljoin("/v1/data/", self.package_path(package))

        params: dict[str, bool | Explain] = {}
        if pretty:
            params['pretty'] = True
        if provenance:
            params['provenance'] = True
        if instrument:
            params['instrument'] = True
        if strict:
            params['strict'] = True
        if metrics:
            params['metrics'] = True
        if explain is not None:
            params['explain'] = explain
        if params:
            raw = True

        resp = self.request(
            "post",
            path,
            "/v1/data",
            json={"input": input},
            params=params,
        )

        if resp.ok:
            decision = resp.json()
            if raw:
                return decision
            if 'result' in decision:
                return decision['result']
            # OPA responds with a successful response even if there's no
            # default policy and the package doesn't exist. We treat that as
            # an error.
            raise PolicyNotFound(f"Policy matching '{package}' not found.")

        raise PolicyRequestError(resp.json())

    def save_document(self, package: str, data: dict):
        path = parse.urljoin("/v1/data/", self.package_path(package))
        resp = self.request(
            "put",
            path,
            "/v1/data",
            json=data,
        )

    def list_documents(self):
        resp = self.request("get", "/v1/data")
        if resp.ok:
            return resp.json()["result"]

    def delete_document(self, package: str) -> dict:
        path = parse.urljoin("/v1/data/", self.package_path(package))
        resp = self.request("delete", path)

        if resp.ok:
            return {}
        if resp.status_code == 404:
            raise DocumentNotFound("Document not found")

        raise ConnectionError("Unable to delete data.")

    def get_document(self, package: str):
        path = parse.urljoin("/v1/data/", self.package_path(package))
        resp = self.request(
            "get",
            path,
            "/v1/data",
        )
        if resp.ok:
            document = resp.json()
            if "result" in document:
                return document["result"]
            raise DocumentNotFound(f"Document not found at '{package}'.")

    # Policy API

    def list_policies(self):
        path = "/v1/policies"
        resp = self.request("get", path)

        if resp.ok:
            return resp.json()['result']

        raise ConnectionError("Unable to retrieve policies.")

    def get_policy(self, id):
        path = parse.urljoin("/v1/policies/", id)
        resp = self.request("get", path)

        if resp.ok:
            return resp.json()["result"]
        if resp.status_code == 404:
            raise PolicyNotFound(resp.json())

        raise ConnectionError("Unable to get policy.")

    def get_default_policy(self):
        """Attempts to retrieve the default policy. Will raise
        `PolicyNotFound` if no policy with the package signature `system`
        could be found.

        """
        resp = self.request("post", "/")

        if resp.ok:
            return resp.json()
        if resp.status_code == 404:
            raise PolicyNotFound(resp.json())

        raise ConnectionError("Unable to get default policy.")

    def save_policy(self, id, policy):
        path = parse.urljoin("/v1/policies/", id)
        resp = self.request("put", path, data=policy)

        if resp.ok:
            return resp.json()
        if resp.status_code == 400:
            raise InvalidPolicy(resp.json())

        raise ConnectionError("Unable to save policy.")

    def delete_policy(self, id):
        path = parse.urljoin("/v1/policies/", id)
        resp = self.request("delete", path)

        if resp.ok:
            return resp.json()
        if resp.status_code == 404:
            raise PolicyNotFound(resp.json())

        raise ConnectionError("Unable to delete policy.")

    # Query API

    def query(self, query: str, input: dict, pretty: bool = False):
        body = {
            "query": query,
            "input": input,
        }
        resp = self.request("post", "/v1/query", json=body)

        if resp.ok:
            return resp.json()
        if resp.status_code == 400:
            raise InvalidPolicy(resp.json())

        raise ConnectionError("Unable to evaluate query.")

    # Config API

    def get_config(self):
        resp = self.request("get", "/v1/config")

        if resp.ok:
            return resp.json()["result"]

        raise ConnectionError("Unable to get configuration.")
