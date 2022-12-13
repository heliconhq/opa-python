import pytest


@pytest.fixture
def policy(client):
    policy = """
    package opa.test

    default allow := false

    allow {
        input.decision = "allow"
    }
    """
    client.save_policy("policy", policy)


def test_package(server, client, policy):
    decision = client.check_policy("opa.test", {"decision": "allow"})
    assert decision["allow"] is True


def test_package_and_rule(server, client, policy):
    decision = client.check_policy("opa.test.allow", {"decision": "allow"})
    assert decision is True


def test_metrics(server, client, policy):
    decision = client.check_policy("opa.test.allow", metrics=True)
    assert "metrics" in decision
