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
    backoff_factor = 0.2

    def __init__(
        self,
        url: str = "http://localhost:8181",
        verify: bool = True,
        retries: int = 5,
        token: typing.Optional[str] = None,
    ):
        """Initialize a new OPA client.

        :param url: (Optional) URL to OPA server. Defaults to
            ``http://localhost:8181``.
        :param verify: (Optional) Dictates whether SSL certificates should be
            verfied or not.
        :param token: (Optional) Token used to authorize client with OPA
            server.
        :param retries: (Optional) Number of times requests should be retried
            before giving up.

        """
        self.url = self.parse_url(url)
        self.verify = verify
        self.token = token
        self.retries = retries

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
        retries: typing.Optional[int] = None,
    ) -> requests.Response:
        """Make a request to OPA server. Used primarily internally.

        :param verb: The HTTP verb to use.
        :param path: Path to make request to.
        :param json: (Optional) JSON serializable object to send.
        :param params: (Optional) Dictionary to send in the query string.
        :param data: (Optional) Arbitrary object to send.
        :param retries: (Optional) Override client retry setting.

        """

        headers = {}
        if self.token is not None:
            headers["Authorization"] = f"Bearer {self.token}"

        url = parse.urljoin(self.url, path)

        with requests.Session() as s:
            max_retries = Retry(
                total=retries if retries is not None else self.retries,
                backoff_factor=self.backoff_factor,
            )
            s.mount(url, HTTPAdapter(max_retries=max_retries))

            try:
                resp = s.request(
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

    def check_health(
        self,
        bundles: bool = False,
        plugins: bool = False,
        exclude_plugins: typing.Optional[list[str]] = None,
        retries: typing.Optional[int] = None,
    ) -> bool:
        """Check that the connection to the OPA server is healthy.

        :param bundles: (Optional) Account for bundles during health check.
        :param plugins: (Optional) Account for plugins during health check.
        :param exclude_plugins: (Optional) Plugins to exclude from check. Only
            valid if `plugins` is true.
        :param retries: (Optional) Override client retry setting.

        """
        params: dict[str, bool | Explain] = {}
        if bundles:
            params['bundles'] = True
        if plugins:
            params['plugins'] = True
        if plugins and exclude_plugins is not None:
            params['exclude-plugins'] = exclude_plugins

        resp = self.request('get', '/health', retries=retries)

        if resp.ok and not resp.json():
            return True

        return False

    def check_liveness(self) -> bool:
        """Check liveness by making sure the `live` rule in the
        `system.health` policy exists and evaluates to true.

        """
        return self.check_custom_health_rule("live")

    def check_readiness(self) -> bool:
        """Check readiness by making sure the `ready` rule in the
        `system.health` policy exists and evaluates to true.

        """
        return self.check_custom_health_rule("ready")

    def check_custom_health_rule(self, rule: str):
        """Run custom rule in the `system.health` policy. The check will fail
        if the rule evaluates to false or does not exist.

        """
        assert '/' not in rule
        assert '.' not in rule
        resp = self.request('get', f'/health/{rule}')

        if resp.ok and not resp.json():
            return True

        return False

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
        """Request a decision for the specified named policy.

        :param package: Package that defines the policy. May include rule name.
        :param input: (Optional) Python dict providing `input` for the policy.
        :param raw: (Optional) Whether to return the raw response or just use
            the result-part of the object returned from the server.
        :param pretty: (Optional) Make the result pretty.
        :param provenance: (Optional) Include provenance information in the
            response. Will always return a `raw` value.
        :param instrument: (Optional) Instrument query evaluation and include
            details in response. Will always return a `raw` value.
        :param strict: (Optional) Treat built-in-function call errors as fatal.
        :param explain: (Optional) Include query explanation in response. Will
            always return a `raw` value.
        :param metrics: (Optional) Include query performance metrics in
            response. Will always return a `raw` value.

        """
        path = parse.urljoin("/v1/data/", self.package_path(package))

        params: dict[str, bool | Explain] = {}
        if pretty:
            params['pretty'] = True
        if provenance:
            params['provenance'] = True
            raw = True
        if instrument:
            params['instrument'] = True
            raw = True
        if strict:
            params['strict-builtin-errors'] = True
        if metrics:
            params['metrics'] = True
            raw = True
        if explain is not None:
            params['explain'] = explain
            raw = True

        resp = self.request("post", path, json={"input": input}, params=params)

        if resp.ok:
            decision = resp.json()

            if raw:
                return typing.cast(Decision, decision)

            if 'result' in decision:
                return typing.cast(Decision, decision['result'])

            # OPA responds with a 2xx status code even when there are runtime
            # errors or if a policy does not exist. We treat that as an error
            # and leave it to the implementor to decide.
            raise PolicyNotFound(f"Policy matching '{package}' not found.")

        raise PolicyRequestError(resp.json())

    def save_document(self, package: str, data: Document) -> None:
        """Create or update a document.

        :param package: Package path used to access the data.
        :param data: JSON serializable object containing data.

        """
        path = parse.urljoin("/v1/data/", self.package_path(package))
        resp = self.request("put", path, json=data)

        if resp.ok:
            return None

        if resp.status_code == 400:
            raise InvalidDocument(resp.json())

        raise ConnectionError("Unable to save document.")

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
