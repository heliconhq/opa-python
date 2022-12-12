import pytest


def test_use_document(server, client):
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
