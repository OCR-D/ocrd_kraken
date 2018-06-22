export

SHELL = /bin/bash
PYTHON = python
PIP = pip
LOG_LEVEL = INFO
PYTHONIOENCODING=utf8

# Docker container tag ("$(DOCKER_TAG)")
DOCKER_TAG = 'ocrd/kraken'

# BEGIN-EVAL makefile-parser --make-help Makefile

help:
	@echo ""
	@echo "  Targets"
	@echo ""
	@echo "    deps-pip       Install python deps via pip"
	@echo "    deps-pip-test  Install testing deps via pip"
	@echo "    install        Install"
	@echo "    docker         Build docker image"
	@echo "    test           Run test"
	@echo "    repo/assets    Clone OCR-D/assets to ./repo/assets"
	@echo "    assets         Setup test assets"
	@echo ""
	@echo "  Variables"
	@echo ""
	@echo "    DOCKER_TAG  Docker container tag ("$(DOCKER_TAG)")"

# END-EVAL

# Install python deps via pip
deps-pip:
	$(PIP) install -r requirements.txt

# Install testing deps via pip
deps-pip-test:
	$(PIP) install -r requirements_test.txt

deps: deps-pip

# Install
install:
	$(PIP) install .

# Build docker image
docker:
	docker build -t $(DOCKER_TAG) .

.PHONY: test
# Run test
test:
	$(PYTHON) -m pytest test

#
# Assets
#

# Clone OCR-D/assets to ./repo/assets
repo/assets:
	mkdir -p $(dir $@)
	git clone https://github.com/OCR-D/assets "$@"


# Setup test assets
assets: repo/assets
	mkdir -p test/assets
	cp -r -t test/assets repo/assets/data/*
