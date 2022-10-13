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
	@echo "    deps         Install python deps via pip"
	@echo "    deps-test    Install testing deps via pip"
	@echo "    install      Install"
	@echo "    docker       Build docker image"
	@echo "    test         Run test"
	@echo "    repo/assets  Clone OCR-D/assets to ./repo/assets"
	@echo "    assets       Setup test assets"
	@echo ""
	@echo "  Variables"
	@echo ""
	@echo "    DOCKER_TAG  Docker container tag ("$(DOCKER_TAG)")"

# END-EVAL

# Install python deps via pip
deps:
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt

deps-ubuntu:
	apt-get update
	apt-get -y install scons libprotobuf-dev protobuf-compiler libpng-dev libeigen3-dev swig

# Install testing deps via pip
deps-test:
	$(PIP) install -r requirements_test.txt

# Install
install:
	$(PIP) install .

install-dev:
	$(PIP) install -e .

# Build docker image
docker:
	docker build \
        --build-arg VCS_REF=$$(git rev-parse --short HEAD) \
        --build-arg BUILD_DATE=$$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
	-t $(DOCKER_TAG) .

# Run test
test: tests/assets
	$(PYTHON) -m pytest tests

#
# Assets
#

# Clone OCR-D/assets to ./repo/assets
repo/assets:
	mkdir -p $(dir $@)
	git clone https://github.com/OCR-D/assets "$@"


# Setup test assets
tests/assets: repo/assets
	mkdir -p tests/assets
	cp -r -t tests/assets repo/assets/data/*

.PHONY: docker install install-dev deps deps-ubuntu deps-test test help
