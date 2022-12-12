import pytest


def test_health_check(server, client):
    health = client.check_health()
    assert health == {}
