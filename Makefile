export

SHELL = /bin/bash
PYTHON = python
PIP = pip
LOG_LEVEL = INFO
PYTHONIOENCODING=utf8

# Docker container tag ("$(DOCKER_TAG)")
DOCKER_TAG = 'ocrd/kraken'
DOCKER_BASE_IMAGE = docker.io/ocrd/core-cuda:v2.70.0


# BEGIN-EVAL makefile-parser --make-help Makefile

help:
	@echo ""
	@echo "  Targets"
	@echo ""
	@echo "    deps         Install python deps via pip"
	@echo "    deps-test    Install testing deps via pip"
	@echo "    deps-ubuntu  Install required packages for Debian/Ubuntu"
	@echo "    install      Install"
	@echo "    install-dev  Install in editable mode"
	@echo "    build        Build source and binary distribution"
	@echo "    docker       Build Docker image"
	@echo "    test         Run test"
	@echo "    repo/assets  Clone OCR-D/assets to ./repo/assets"
	@echo "    tests/assets       Setup test assets"
	@echo ""
	@echo "  Variables"
	@echo ""
	@echo "    DOCKER_TAG  Docker container tag ("$(DOCKER_TAG)")"
	@echo "    PYTEST_ARGS Additional runtime options for pytest ("$(PYTEST_ARGS)")"

# END-EVAL

# Install python deps via pip
deps:
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt

deps-ubuntu:
ifeq ($(shell type -p apt-get), /usr/bin/apt-get)
	apt-get update
	apt-get -y install libprotobuf-dev protobuf-compiler libpng-dev libeigen3-dev
endif

# Install testing deps via pip
deps-test:
	$(PIP) install -r requirements_test.txt

# Install
install:
	$(PIP) install .

install-dev:
	$(PIP) install -e .

build:
	$(PIP) install build
	$(PYTHON) -m build .

# Build docker image
docker:
	docker build \
	--build-arg DOCKER_BASE_IMAGE=$(DOCKER_BASE_IMAGE) \
	--build-arg VCS_REF=$$(git rev-parse --short HEAD) \
	--build-arg BUILD_DATE=$$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
	-t $(DOCKER_TAG) .

# Run test
test: tests/assets
	$(PYTHON) -m pytest tests $(PYTEST_ARGS)

#
# Assets
#

# Update OCR-D/assets submodule
.PHONY: repos always-update tests/assets
repo/assets: always-update
	git submodule sync --recursive $@
	if git submodule status --recursive $@ | grep -qv '^ '; then \
		git submodule update --init --recursive $@ && \
		touch $@; \
	fi


# Setup test assets
tests/assets: repo/assets
	mkdir -p tests/assets
	cp -a repo/assets/data/* tests/assets

.PHONY: docker install install-dev deps deps-ubuntu deps-test test help
