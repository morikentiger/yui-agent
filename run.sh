#!/bin/bash
cd "$(dirname "$0")"
PYTHONPATH="$(pwd)" python3.11 -m yui.cli
