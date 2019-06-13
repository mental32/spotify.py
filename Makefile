PYTHON := python3
LINTER := flake8

.PHONY: install pypi test lint

install:
	$(PYTHON) setup.py install --user

test:
	$(PYTHON) -m unittest discover -s test

pypi:
	$(PYTHON) setup.py sdist
	twine upload dist/*

lint:
	@$(LINTER) spotify > spotify.$(LINTER)
