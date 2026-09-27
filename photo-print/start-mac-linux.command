#!/bin/sh
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  echo "First run: installing..."
  python3 -m venv .venv && .venv/bin/pip install --upgrade pip >/dev/null && .venv/bin/pip install -r requirements.txt || exit 1
fi
exec .venv/bin/python -m photoprint "$@"
