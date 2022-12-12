class OPAException(Exception):
    pass


class InvalidURL(OPAException):
    pass


class ConnectionError(OPAException):
    pass


class Unauthorized(OPAException):
    pass


class InvalidPolicy(OPAException):
    pass


class InvalidPolicyRequest(OPAException):
    pass


class PolicyRequestError(OPAException):
    pass


class PolicyNotFound(OPAException):
    pass


class DocumentNotFound(OPAException):
    pass


class Unauthorized(OPAException):
    pass
