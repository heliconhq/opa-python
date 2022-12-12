import pytest

from opa import exceptions


def test_unauthorized_policy_list(token_auth_server, client):
    with pytest.raises(exceptions.Unauthorized) as e:
        client.list_policies()


def test_authorized_policy_list(token_auth_server, token_auth_client):
    policies = token_auth_client.list_policies()
    assert len(policies) == 1
