class OPAException(Exception):
    """Base exception all other `opa-client` exceptions are derived from."""


class InvalidURL(OPAException):
    """The URL was somehow invalid."""


class ConnectionError(OPAException):
    """Generic connection error."""


class InvalidPolicy(OPAException):
    """The policy provided was not valid."""


class InvalidDocument(OPAException):
    """The document provided was not valid."""


class InvalidPolicyRequest(OPAException):
    """The policy-request was not valid."""


class PolicyRequestError(OPAException):
    """There was an error requesting the policy."""


class PolicyNotFound(OPAException):
    """The policy could not be found."""


class DocumentNotFound(OPAException):
    """The document could not be found."""


class Unauthorized(OPAException):
    """The request to OPA was not authorized."""
