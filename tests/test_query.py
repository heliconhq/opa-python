def test_query(server, client):
    query = """
    input.servers[i].protocol = \"http\"
    input.servers[i].name = name
    """
    result = client.query(
        query,
        {
            "servers": [
                {
                    "name": "rivendell",
                    "protocol": "http"
                },
                {
                    "name": "rohan",
                    "protocol": "http"
                },
                {
                    "name": "arda",
                    "protocol": "ftp"
                },
            ]
        },
    )
    assert len(result["result"]) == 2
