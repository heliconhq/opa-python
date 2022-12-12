# OPA Python

Simple client for Open Policy Framework (OPA).

Under construction :)

## Installation

Using pip:

    pip install opa-python
    
Using Poetry:

    poetry add opa-python

## Usage

See `./tests` for now :)

## Running the test suite

NOTE: Each individual test that communicates with OPA creates a fresh Docker
container. This is pretty neat from a testing perspective, but means that
running the entire suite takes a bit of time.

Make sure you do not have any services listening to `8181` when you start the
tests! We might add a configuration for setting the port later, or run the
tests in Docker as well.

First make sure you have [Poetry](https://python-poetry.org/) installed.

Create new environment and install the dependencies:

    poetry install
    
Run the tests:

    poetry run pytest
    
Run specific test module:

    poetry run pytest tests/test_integration.py
