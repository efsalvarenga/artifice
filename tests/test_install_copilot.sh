#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
exec python3 -m unittest discover -s "$root/tests" -p 'test_install_copilot.py' -v
