Introduction
============

Installation
------------

You can install `opa-python` with `pip`::

    python -m pip install requests

Compatibiity
------------

The library has been tested wtih:

* Python 3.10
* OPA 0.47.3

Get the source code
-------------------

The source code is available on `GitHub <https://github.com/heliconhq/opa-python>`_.

Usage
-----

Create a client instance:

.. code-block:: python

    from opa import OPAClient
    client = OPAClient(url="http://opa-server/")

Verify that the OPA server is up and ready to accept requests:

.. code-block:: python

    client.check_health()
    
Create or update a document:

.. code-block:: python

    data = {
        "users": [
            "bilbo",
            "frodo",
            "gandalf",
        ],
    }
    client.save_document("my.data", data)
    
Create or update a policy:

.. code-block:: python

    policy = """
    package my.policy

    default allow := false

    allow {
        data.my.data.users[_] = input.name
    }
    """
    client.save_policy("policy-id", policy)
    
Request decisions by evaluating input against the policy and data:

.. code-block:: python

    client.check_policy("my.policy.allow", {"name": "bilbo"})
    client.check_policy("my.policy.allow", {"name": "sauron"})
