PY ?= .venv/bin/python
T ?= tests

.PHONY: install test vendored vendored-verify validate-real

install:
	uv venv --allow-existing --python 3.12 .venv
	uv pip install --python $(PY) -e '.[dev]'

test:
	$(PY) -m pytest -q $(T)

vendored:
	$(PY) scripts/fetch_vendored.py

vendored-verify:
	$(PY) scripts/fetch_vendored.py --verify-only

validate-real:
	$(PY) -m watermark_detector validate tests/fixtures/real/expected.json
