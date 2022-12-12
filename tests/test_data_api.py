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


def test_get_policy(client):
    policy = client.get_policy("id")
    assert "ast" in policy
    assert policy["id"] == "id"


def test_no_default_policy(client):
    with pytest.raises(exceptions.PolicyNotFound) as e:
        client.get_default_policy()


def test_get_default_policy(client):
    policy = """
    package system

    main = "welcome!"
    """
    client.save_policy("default", policy)
    policy = client.get_default_policy()
    assert policy == "welcome!"


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


def test_save_document(client):
    data = {
        "servers": [
            "a",
            "b",
            "c",
        ]
    }
    result = client.save_document("my.data", data)
    assert result is None


def test_list_documents(client):
    result = client.list_documents()
    assert "my" in result
    assert "opa" in result


def test_get_document(client):
    result = client.get_document("my.data")
    assert len(result["servers"]) == 3


# def test_delete_document(client):
#     result = client.get_document("my.data")
#     assert len(result["servers"]) == 3
#     client.delete_document("my.data")
#     result = client.list_documents()
#     assert "my" not in result

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


def test_use_document(client):
    data = {
        "users": [
            "bilbo",
            "frodo",
            "gandalf",
        ],
    }
    client.save_document("integration", data)

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
