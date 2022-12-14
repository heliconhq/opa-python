import pytest

from opa import exceptions


@pytest.fixture
def policy(client):
    policy = """
    package opa.test

    default allow := false

    allow {
        input.decision = "allow"
    }

    rte {
        1 / 0
    }
    """
    client.save_policy("policy", policy)


def test_package(server, client, policy):
    decision = client.check_policy("opa.test", {"decision": "allow"})
    assert decision["allow"] is True

    decision = client.check_policy("opa.test", {"decision": "deny"})
    assert decision["allow"] is False


def test_package_and_rule(server, client, policy):
    decision = client.check_policy("opa.test.allow", {"decision": "allow"})
    assert decision is True

    decision = client.check_policy("opa.test.allow", {"decision": "deny"})
    assert decision is False


def test_metrics(server, client, policy):
    decision = client.check_policy("opa.test.allow", metrics=True)
    assert "metrics" in decision


def test_instrument(server, client, policy):
    decision = client.check_policy("opa.test.allow", metrics=True)
    assert "metrics" in decision


def test_explain(server, client, policy):
    decision = client.check_policy("opa.test.allow", explain='notes')
    assert "explanation" in decision


def test_without_input(server, client, policy):
    decision = client.check_policy("opa.test.allow")
    assert decision is False


def test_without_input_raw(server, client, policy):
    decision = client.check_policy("opa.test.allow", raw=True)
    assert "warning" in decision
    assert decision["result"] is False


def test_runtime_error(server, client, policy):
    with pytest.raises(exceptions.PolicyNotFound) as e:
        decision = client.check_policy(
            "opa.test.rte",
            {"decision": "allow"},
            strict=False,
        )


def test_runtime_error_strict(server, client, policy):
    with pytest.raises(exceptions.PolicyRequestError) as e:
        decision = client.check_policy(
            "opa.test.rte",
            {"decision": "allow"},
            strict=True,
        )
    assert e.value.args[0]["code"] == "internal_error"
