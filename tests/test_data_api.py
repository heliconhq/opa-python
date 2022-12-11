import pytest

from opa import OPAClient
from opa import exceptions

# NOTE: There's no teardown / reset between the tests. We rely on the tests
# running in order until we have something else set up.


@pytest.fixture
def client():
    c = OPAClient(url='http://opa:8181/')
    # We check the health first as it will wait for the OPA server to be up
    # and ready to accept requests.
    c.check_health()
    return c


# Policy API


def test_no_policies(client):
    policies = client.list_policies()
    assert len(policies) == 0


def test_create_policy(client):
    policy = """
    package opa.test

    default allow := false

    allow {
        input.decision = "allow"
    }

    """
    client.save_policy("id", policy)
    policies = client.list_policies()
    assert len(policies) == 1


def test_create_empty_policy(client):
    with pytest.raises(exceptions.InvalidPolicy) as e:
        client.save_policy("id", "")


def test_list_again(client):
    policies = client.list_policies()
    assert len(policies) == 1


def test_delete_policy(client):
    client.delete_policy("id")
    policies = client.list_policies()
    assert len(policies) == 0


def test_delete_policy(client):
    with pytest.raises(exceptions.PolicyNotFound) as e:
        # OPA does not return a 404 when you try to delete a policy that
        # you've already deleted.
        client.delete_policy("id2")


# Data API


def test_save_data(client):
    data = {
        "servers": [
            "a",
            "b",
            "c",
        ]
    }
    result = client.save_data("my.data", data)
    assert result is None


def test_get_data(client):
    result = client.get_data("my.data")
    assert len(result["servers"]) == 3


# Query API


def test_query(client):
    query = """
    input.servers[_].protocol = \"http\"
    input.servers[i].name = name
    """
    result = client.query(
        query,
        {"servers": [{
            "name": "a",
            "protocol": "http"
        }]},
    )
    assert result["result"] == [{"i": 0, "name": "a"}]


# Integration


def test_use_data(client):
    data = {
        "users": [
            "bilbo",
            "frodo",
            "gandalf",
        ],
    }
    client.save_data("integration", data)

    policy = """
    package integration

    default allow := false

    allow {
        data.integration.users[_] = input.name
    }

    """
    client.save_policy("integration", policy)

    decision = client.check_policy({"name": "bilbo"}, "integration.allow")
    assert decision is True

    decision = client.check_policy({"name": "sauron"}, "integration.allow")
    assert decision is False
