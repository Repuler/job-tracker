.PHONY: install test

install:
	.venv/bin/python -m pip install -r requirements.txt

test:
	.venv/bin/python -m pytest -q
