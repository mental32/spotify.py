PYTHON := python3
LINTER := flake8

FORMATTER := black
FORMATTER_ARGS := -S

.PHONY: install pypi test lint clean format

clean:
	@rm -rf dist spotify.egg*

install:
	$(PYTHON) setup.py install --user

test:
	$(PYTHON) -m unittest discover -s test

format:
	$(FORMATTER) $(FORMATTER_ARGS) spotify

pypi: clean format
	$(PYTHON) setup.py sdist
	twine upload dist/*

lint:
	@$(LINTER) spotify > spotify.$(LINTER)
