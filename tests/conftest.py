import os
import time

import docker
import pytest

from opa import OPAClient

AUTH_TOKEN = "secret"
OPA_VERSION = "0.47.3"
PORT = 8181


def start_container(command):
    client = docker.from_env()
    dir = os.path.dirname(os.path.realpath(__file__))
    policy_path = os.path.join(dir, "system.rego")
    container = client.containers.run(
        f"openpolicyagent/opa:{OPA_VERSION}-rootless",
        command,
        ports={f"{PORT}/tcp": PORT},
        name="opa-test-2",
        volumes=[
            f"{policy_path}:/system.rego",
        ],
        detach=True,
    )
    return container


@pytest.fixture
def server():
    """Start a regular server without authorization."""
    container = start_container([
        "run",
        "--server",
        "--set=decision_logs.console=true",
        "system.rego",
    ])
    time.sleep(1)
    yield container
    container.kill()
    container.remove()


@pytest.fixture
def token_auth_server():
    """Start a server with token authorization."""
    container = start_container([
        "run",
        "--server",
        "--set=decision_logs.console=true",
        "--authentication=token",
        "--authorization=basic",
        "system.rego",
    ])
    time.sleep(1)
    yield container
    container.kill()
    container.remove()


@pytest.fixture
def client():
    """Create a client without authorization."""
    client = OPAClient(url='http://localhost:8181/')
    return client


@pytest.fixture
def token_auth_client():
    """Create a client that uses a token for authorization purposes."""
    client = OPAClient(url='http://localhost:8181/', token=AUTH_TOKEN)
    return client
