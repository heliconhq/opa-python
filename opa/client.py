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
Policy = dict[str, typing.Any]
Config = dict[str, typing.Any]
QueryResponse = dict[str, typing.Any]
Document = dict[str, typing.Any]
Decision = dict[str, typing.Any]
HealthReport = dict[str, typing.Any]
Input = dict[str, typing.Any]


class OPAClient:
    timeout = 15000

    def __init__(
        self,
        url: str = "http://localhost:8181",
        verify: bool = True,
        token: typing.Optional[str] = None,
    ):
        """Initialize a new OPA client.

        :param url: (Optional) URL to OPA server. Defaults to
            ``http://localhost:8181``.
        :param verify: (Optional) Dictates whether SSL certificates should be
            verfied or not.
        :param token: (Optional) Token used to authorize client with OPA
            server.

        """
        self.url = self.parse_url(url)
        self.verify = verify
        self.token = token

    def parse_url(self, url: str) -> str:
        """Parse and perform basic validation of supplied `url`.

        :url: URL to parse. With or without scheme.

        """
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

    def package_path(self, package: str) -> str:
        """Normalize and return a package path that can be used in HTTP
        requests. Replaces '.' with '/' and strips leading slash.

        :param package: Package path to normalize.

        """
        return package.replace(".", "/").lstrip("/")

    def request(
        self,
        verb: str,
        path: str,
        json: typing.Any = None,
        params: typing.Any = None,
        data: typing.Any = None,
    ) -> requests.Response:
        """Make a request to OPA server. Used primarily internally.

        :param verb: The HTTP verb to use.
        :param path: Path to make request to.
        :param json: (Optional) JSON serializable object to send.
        :param params: (Optional) Dictionary to send in the query string.
        :param data: (Optional) Arbitrary object to send.

        """

        headers = {}
        if self.token is not None:
            headers["Authorization"] = f"Bearer {self.token}"

        url = parse.urljoin(self.url, path)

        try:
            resp = requests.request(
                verb,
                url,
                headers=headers,
                timeout=self.timeout,
                verify=self.verify,
                json=json,
                data=data,
                params=params,
            )

            if resp.status_code == 401:
                raise Unauthorized(resp.json())

            return resp
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Unable to connect to OPA server.")

    def check_health(self) -> HealthReport:
        """Check that the connection to the OPA server is healthy."""
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
                return typing.cast(HealthReport, resp.json())

            if resp.status_code == 401:
                raise Unauthorized(resp.json())

            raise ConnectionError("Connection not healthy.")

    # Data API

    def check_policy(
        self,
        package: str,
        input: typing.Optional[Input] = None,
        raw: bool = False,
        pretty: bool = False,
        provenance: bool = False,
        instrument: bool = False,
        strict: bool = False,
        explain: typing.Optional[Explain] = None,
        metrics: bool = False,
    ) -> Decision:
        """Get a decision for the specified named policy.

        :param package: Package that defines the policy. May include rule name.
        :param input: (Optional) Python dict providing `input` for the policy.
        :param raw: (Optional) Whether to return the raw response or not.
        :param pretty: (Optional) Make the result pretty.
        :param provenance: (Optional) Include provenance information in the
            response.
        :param instrument: (Optional) Instrument query evaluation and include
            details in response.
        :param strict: (Optional) Treat built-in-function call errors as fatal.
        :param explain: (Optional) Include query explanation in response.
        :param metrics: (Optional) Include query performance metrics in
            response.

        """
        path = parse.urljoin("/v1/data/", self.package_path(package))

        params: dict[str, bool | Explain] = {}
        if pretty:
            params['pretty'] = True
        if provenance:
            params['provenance'] = True
        if instrument:
            params['instrument'] = True
        if strict:
            params['strict-builtin-errors'] = True
        if metrics:
            params['metrics'] = True
        if explain is not None:
            params['explain'] = explain
        if params:
            raw = True

        resp = self.request(
            "post",
            path,
            json={"input": input},
            params=params,
        )

        if resp.ok:
            decision = resp.json()
            if raw:
                return typing.cast(Decision, decision)
            if 'result' in decision:
                return typing.cast(Decision, decision['result'])
            # OPA responds with a successful response even if there's no
            # default policy and the package doesn't exist. We treat that as
            # an error.
            raise PolicyNotFound(f"Policy matching '{package}' not found.")

        raise PolicyRequestError(resp.json())

    def save_document(self, package: str, data: Document) -> None:
        """Create or update a document.

        :param package: Package path used to access the data.
        :param data: JSON serializable object containing data.

        """
        path = parse.urljoin("/v1/data/", self.package_path(package))
        resp = self.request(
            "put",
            path,
            json=data,
        )

    def list_documents(self) -> list[Document]:
        """List all available documents."""
        resp = self.request("get", "/v1/data")
        if resp.ok:
            return typing.cast(list[Document], resp.json()["result"])
        raise ConnectionError("Unable to list documents.")

    def delete_document(self, package: str) -> dict[str, typing.Any]:
        """Delete a document.

        :param package: Package path to the document.

        """
        path = parse.urljoin("/v1/data/", self.package_path(package))
        resp = self.request("delete", path)

        if resp.ok:
            return {}
        if resp.status_code == 404:
            raise DocumentNotFound("Document not found")

        raise ConnectionError("Unable to delete document.")

    def get_document(self, package: str) -> Document:
        """Find and return a document.

        :param package: Package path to the document.

        """
        path = parse.urljoin("/v1/data/", self.package_path(package))
        resp = self.request("get", path)
        if resp.ok:
            document = resp.json()
            if "result" in document:
                return typing.cast(Document, document["result"])
            raise DocumentNotFound(f"Document not found at '{package}'.")
        raise ConnectionError("Unable to get document.")

    # Policy API

    def list_policies(self) -> list[Policy]:
        """List all policies."""
        path = "/v1/policies"
        resp = self.request("get", path)

        if resp.ok:
            return typing.cast(list[Policy], resp.json()['result'])

        raise ConnectionError("Unable to retrieve policies.")

    def get_policy(self, id: str) -> Policy:
        """Get a specific policy.

        :param id: Id of the policy.

        """
        path = parse.urljoin("/v1/policies/", id)
        resp = self.request("get", path)

        if resp.ok:
            return typing.cast(Policy, resp.json()["result"])
        if resp.status_code == 404:
            raise PolicyNotFound(resp.json())

        raise ConnectionError("Unable to get policy.")

    def get_default_policy(self) -> Policy:
        """Attempts to retrieve the default policy. Will raise
        `PolicyNotFound` if no policy with the package signature `system`
        could be found.

        """
        resp = self.request("post", "/")

        if resp.ok:
            return typing.cast(Policy, resp.json())
        if resp.status_code == 404:
            raise PolicyNotFound(resp.json())

        raise ConnectionError("Unable to get default policy.")

    def save_policy(self, id: str, policy: str) -> Policy:
        """Create or update a policy.

        :param id: Id of the policy.
        :param policy: Policy written in rego.

        """
        path = parse.urljoin("/v1/policies/", id)
        resp = self.request("put", path, data=policy)

        if resp.ok:
            return typing.cast(Policy, resp.json())
        if resp.status_code == 400:
            raise InvalidPolicy(resp.json())

        raise ConnectionError("Unable to save policy.")

    def delete_policy(self, id: str) -> dict[str, typing.Any]:
        """Delete a policy.

        :param id: Id of the policy.

        """
        path = parse.urljoin("/v1/policies/", id)
        resp = self.request("delete", path)

        if resp.ok:
            return typing.cast(dict[str, typing.Any], resp.json())
        if resp.status_code == 404:
            raise PolicyNotFound(resp.json())

        raise ConnectionError("Unable to delete policy.")

    # Query API

    def query(
        self,
        query: str,
        input: dict[str, typing.Any],
        pretty: bool = False,
        explain: typing.Optional[Explain] = None,
        metrics: bool = False,
    ) -> QueryResponse:
        """Execute an ad-hoc query and return bindings for variables found in
        the query.

        :param query: The query to execute.
        :param input: Python dict providing `input` for the query.
        :param pretty: (Optional) Make the result pretty.
        :param explain: (Optional) Include query explanation in response.
        :param metrics: (Optional) Include query performance metrics in
            response.

        """
        body = {
            "query": query,
            "input": input,
        }

        params: dict[str, bool | Explain] = {}
        if pretty:
            params['pretty'] = True
        if explain is not None:
            params['explain'] = explain
        if metrics:
            params['metrics'] = True

        resp = self.request("post", "/v1/query", json=body, params=params)

        if resp.ok:
            return typing.cast(QueryResponse, resp.json())
        if resp.status_code == 400:
            raise InvalidPolicy(resp.json())

        raise ConnectionError("Unable to evaluate query.")

    # Config API

    def get_config(self) -> Config:
        """Return OPA's active configuration as a dict."""
        resp = self.request("get", "/v1/config")

        if resp.ok:
            return typing.cast(Config, resp.json()["result"])

        raise ConnectionError("Unable to get configuration.")
