import pytest

from opa import exceptions

POLICY = """
package opa.test

default allow := false

allow {
    input.decision = "allow"
}

"""


def test_only_system_policy(server, client):
    policies = client.list_policies()
    # Assume one policy as we include a default `system.authz` policy when OPA
    # is started.
    assert len(policies) == 1


def test_create_policy(server, client):
    client.save_policy("policy-id", POLICY)
    policies = client.list_policies()
    assert len(policies) == 2


def test_create_empty_policy(server, client):
    with pytest.raises(exceptions.InvalidPolicy) as e:
        client.save_policy("id", "")
    policies = client.list_policies()
    assert len(policies) == 1


def test_create_invalid_policy(server, client):
    client.save_policy("id-1", POLICY)
    with pytest.raises(exceptions.InvalidPolicy) as e:
        # This should fail because rego does not allow multiple default rules
        # in the same package (`allow` in this case).
        client.save_policy("id-2", POLICY)
    policies = client.list_policies()
    assert len(policies) == 2


def test_get_policy(server, client):
    client.save_policy("policy-id", POLICY)
    policy = client.get_policy("policy-id")
    assert "ast" in policy
    assert policy["id"] == "policy-id"


def test_list_policies(server, client):
    policy_1 = """
    package opa.first

    default allow := false
    """
    client.save_policy("policy-id-1", policy_1)

    policy_2 = """
    package opa.second

    default allow := false
    """
    client.save_policy("policy-id-2", policy_2)

    policies = client.list_policies()

    assert len(policies) == 3


def test_get_default_policy(server, client):
    policy = """
    package system

    main = "welcome!"
    """
    client.save_policy("default", policy)
    policy = client.get_default_policy()
    assert policy == "welcome!"


def test_delete_policy(server, client):
    policies = client.list_policies()
    assert len(policies) == 1

    client.save_policy("policy-id", POLICY)
    policies = client.list_policies()
    assert len(policies) == 2

    client.delete_policy("policy-id")
    policies = client.list_policies()
    assert len(policies) == 1


def test_delete_policy_that_does_not_exist(server, client):
    with pytest.raises(exceptions.PolicyNotFound) as e:
        client.delete_policy("bombadill")
