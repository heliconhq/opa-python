# OPA Python

Python client library for Open Policy Framework (OPA).

## Installation

    python -m pip install opa-python
    
## Compatibility

The library has been tested with:

- Python 3.10
- OPA 0.40.0
    
## Usage

Create a client instance:

```python
from opa import OPAClient
client = OPAClient(url="http://opa-server/")
```

Verify that the OPA server is up and ready to accept requests:

```python
client.check_health()
```
    
Create or update a document:

```python
data = {
    "users": [
        "bilbo",
        "frodo",
        "gandalf",
    ],
}
client.save_document("my.data", data)
```
    
Create or update a policy:

```python
policy = """
package my.policy

default allow := false

allow {
    data.my.data.users[_] = input.name
}
"""
client.save_policy("policy-id", policy)
```
    
Request decisions by evaluating input against the policy and data:

```python
client.check_policy("my.policy.allow", {"name": "bilbo"})
client.check_policy("my.policy.allow", {"name": "sauron"})
```

We're working on the documentation. Please refer to the tests or source code
in the meantime.
    
## Local installation

Install [Poetry](https://python-poetry.org/), create new environment and
install the dependencies:

    poetry install
    
## Running the test suite

NOTE: Each individual test that communicates with OPA creates a fresh Docker
container. This is pretty neat from a testing perspective, but means that
running the entire suite takes a bit of time.

Make sure you do not have any services listening to `8181` when you start the
tests! We might add a configuration for setting the port later, or run the
tests in Docker as well.

Run the tests:

    poetry run pytest
    
Run specific test module:

    poetry run pytest tests/test_integration.py
    
## Publishing

Set your credentials:

    poetry config pypi-token.pypi <token>

Build and publish:

    poetry publish --build
