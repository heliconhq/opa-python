def test_use_document(server, client):
    data = {
        "users": [
            "bilbo",
            "frodo",
            "gandalf",
        ],
    }
    client.save_document("my.data", data)

    policy = """
    package use.document

    default allow := false

    allow {
        data.my.data.users[_] = input.name
    }

    """
    client.save_policy("use.document", policy)

    decision = client.check_policy("use.document.allow", {"name": "bilbo"})
    assert decision is True

    decision = client.check_policy("use.document.allow", {"name": "sauron"})
    assert decision is False


def test_without_input(server, client):
    policy = """
    package without.input

    default allow := true
    """
    client.save_policy("without.input", policy)

    decision = client.check_policy("without.input.allow", {})
    assert decision is True

    decision = client.check_policy("without.input.allow")
    assert decision is True
