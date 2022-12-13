def test_health_check(server, client):
    health = client.check_health()
    assert health is True


def test_health_check_bundles(server, client):
    health = client.check_health(bundles=True)
    assert health is True


def test_health_check_plugins(server, client):
    health = client.check_health(plugins=True)
    assert health is True


def test_check_live_false(server, client):
    live = client.check_live()
    assert live is False


def test_check_live_true(server, client):
    policy = """
    package system.health

    default live = true
    """
    client.save_policy("liveness", policy)
    live = client.check_live()
    assert live is True


def test_check_ready_false(server, client):
    ready = client.check_ready()
    assert ready is False


def test_check_ready_true(server, client):
    policy = """
    package system.health

    default ready = true
    """
    client.save_policy("readiness", policy)
    ready = client.check_ready()
    assert ready is True
