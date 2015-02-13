.PHONY: clean pep8 test build

build: test
	python setup.py sdist
clean:
	python setup.py clean
	@rm -rf *.egg-info/
	@rm -rf dist/
pep8:
	python setup.py pep8
test: clean pep8
	python setup.py test

