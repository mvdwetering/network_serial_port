#!/bin/sh
pytest --cov=custom_components/network_serial_port tests/ --cov-report term-missing --cov-report html
mypy custom_components  --check-untyped-defs
