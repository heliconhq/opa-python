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
    policies = client.list_policies()
    # There should be two policies in the system: id and default.
    assert len(policies) == 2

    client.delete_policy("id")

    policies = client.list_policies()
    assert len(policies) == 1


def test_delete_already_deleted_policy(client):
    with pytest.raises(exceptions.PolicyNotFound) as e:
        client.delete_policy("id")


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
    # assert "opa" in result


def test_get_document(client):
    result = client.get_document("my.data")
    assert len(result["servers"]) == 3


def test_get_document_that_does_not_exist(client):
    with pytest.raises(exceptions.DocumentNotFound) as e:
        client.get_document("isengard")


def test_delete_document(client):
    result = client.get_document("my.data")
    assert len(result["servers"]) == 3

    client.delete_document("my")

    result = client.list_documents()
    assert "my" not in result


def test_delete_document_that_does_not_exist(client):
    with pytest.raises(exceptions.DocumentNotFound) as e:
        client.delete_document("isengard")


def test_delete_document(client):
    result = client.get_document("my.data")
    assert len(result["servers"]) == 3

    client.delete_document("my")

    result = client.list_documents()
    assert "my" not in result


# Query API


def test_query(client):
    query = """
    input.servers[i].protocol = \"http\"
    input.servers[i].name = name
    """
    result = client.query(
        query,
        {
            "servers": [
                {
                    "name": "a",
                    "protocol": "http"
                },
                {
                    "name": "b",
                    "protocol": "http"
                },
                {
                    "name": "c",
                    "protocol": "ftp"
                },
            ]
        },
    )
    assert len(result["result"]) == 2


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
