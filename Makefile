PYTHON := python3
PIP := pip3
LINTER := flake8

FORMATTER := black

.PHONY: install pypi test lint clean format doc mypy

install:
	$(PIP) install -U .

clean:
	@rm -rf dist spotify.egg* build .mypy_*

mypy:
	mypy spotify

doc:
	cd docs && make html

test:
	$(PYTHON) -m unittest discover -s tests

format:
	$(FORMATTER) spotify

pypi: clean format
	$(PYTHON) setup.py sdist
	twine upload dist/*

lint:
	-$(LINTER) ./spotify > spotify.$(LINTER)
