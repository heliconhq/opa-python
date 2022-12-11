import pytest

from opa import OPAClient
from opa import exceptions


def test_no_args():
    """Make sure default arguments work."""
    c = OPAClient()
    assert c.url == "http://localhost"


def test_no_scheme():
    """Client should automatically prepend a scheme if it is missing."""
    c = OPAClient(url="localhost")
    assert c.url == "http://localhost"


def test_https():
    c = OPAClient(url="https://example.com/")
    assert c.url == "https://example.com/"


def test_http():
    c = OPAClient(url="http://example.com/")
    assert c.url == "http://example.com/"


def test_no_hostname():
    with pytest.raises(exceptions.InvalidURL) as e:
        c = OPAClient(url="")
    assert str(e.value) == "Malformed URL. Missing hostname."


def test_invalid_scheme():
    with pytest.raises(exceptions.InvalidURL) as e:
        c = OPAClient(url="ftp://example.com/")
    assert str(e.value) == "Invalid scheme 'ftp'."


def test_invalid_url_type():
    with pytest.raises(exceptions.InvalidURL) as e:
        c = OPAClient(url=1)
    assert str(e.value) == "Invalid URL type."
