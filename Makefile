PYTHON := python3
LINTER := flake8

FORMATTER := black

.PHONY: install pypi test lint clean format

clean:
	@rm -rf dist spotify.egg*

install:
	$(PYTHON) setup.py install --user

test:
	$(PYTHON) -m unittest discover -s test

format:
	$(FORMATTER) spotify

pypi: clean format
	$(PYTHON) setup.py sdist
	twine upload dist/*

lint:
	-$(LINTER) ./spotify > spotify.$(LINTER)
