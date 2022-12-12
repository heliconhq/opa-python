import pytest

from opa import exceptions

DOCUMENT = {
    "servers": [
        "arnor",
        "gondolin",
        "beleriand",
    ]
}


def test_save_document(server, client):
    client.save_document("my.data", DOCUMENT)
    result = client.list_documents()
    assert 'my' in result


def test_list_documents(server, client):
    result = client.list_documents()
    assert result == {}


def test_get_document(server, client):
    client.save_document("my.data", DOCUMENT)
    result = client.get_document("my.data")
    assert len(result["servers"]) == 3


def test_get_document_that_does_not_exist(server, client):
    with pytest.raises(exceptions.DocumentNotFound) as e:
        client.get_document("isengard")


def test_delete_document(server, client):
    client.save_document("my.data", DOCUMENT)
    result = client.get_document("my.data")
    assert len(result["servers"]) == 3

    client.delete_document("my")

    result = client.list_documents()
    assert "my" not in result


def test_delete_document_that_does_not_exist(server, client):
    with pytest.raises(exceptions.DocumentNotFound) as e:
        client.delete_document("rohan")
