#!/bin/bash
pytest --no-header -v --cov=eric_sse --ignore=examples
rm .coverage
