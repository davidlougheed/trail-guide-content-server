#!/usr/bin/env bash

poetry run pytest -svv --cov=trail_guide_content_server --cov-report html --cov-report term
