# OPA Python

Simple client for Open Policy Framework (OPA). Under construction :)

## Installation

TBA.

## Usage

See tests for now :)

## Running the test suite

    make test
    
## Oddities

- Are we really meant to check for decisions by using a `POST` to
  `/v1/data/<package>`? Seems like a weird API.
- Deleting a policy twice does not return a `404` from the OPA server.
