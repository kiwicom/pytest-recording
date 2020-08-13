UPGRADE_ARGS ?= --upgrade

.PHONY: upgrade-requirements
upgrade-requirements:  ## Upgrade requirements to latest versions (use UPGRADE_ARGS='-P <package>' to upgrade one)
	pip install pip-tools
	pip-compile $(UPGRADE_ARGS) --output-file=./requirements.txt requirements.in
	pip-compile $(UPGRADE_ARGS) --output-file=./test-requirements.txt test-requirements.in

test:
	ARCHFLAGS="-arch x86_64" pip install -r ./requirements.txt
	pytest tests -v

tox-test:
	tox -p all

pylint:
	tox -e pylint

black:
	black -l 120 src/pytest_recording docs tests setup.py

mypy:
	mypy --config-file ./mypy.ini src/pytest_recording

install:
	ARCHFLAGS="-arch x86_64" pip install -r ./requirements.txt

build:
	pip install wheel
	python setup.py bdist_wheel

release: build
	pip install twine
	twine check dist/*
	twine upload dist/*

.PHONY: test black install build release
