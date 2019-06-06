PYTHON := python3

.PHONY: install pypi test

install:
	$(PYTHON) setup.py install --user

test:
	$(PYTHON) -m unittest discover -s test

pypi:
	$(PYTHON) setup.py sdist
	twine upload dist/*
