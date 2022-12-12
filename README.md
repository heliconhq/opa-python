# OPA Python

Simple client for Open Policy Framework (OPA). Under construction :)

## Installation

TBA.

## Usage

See tests for now :)

## Running the test suite

NOTE: Each individual test that communicates with OPA creates a fresh Docker
container. This is pretty neat from a testing perspective, but means that
running the entire suite takes a bit of time.

Make sure you do not have any services listening to `8181` when you start the
tests! We might add a configuration for setting the port later, or run the
tests in Docker as well.

Create and activate a new environment:

    python -m venv env
    source ./env/bin/activate
    
Install the deps:

    pip install -r requirements.txt
    
Run the tests:

    pytest
