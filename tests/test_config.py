def test_get_config(server, client):
    config = client.get_config()
    assert "decision_logs" in config
