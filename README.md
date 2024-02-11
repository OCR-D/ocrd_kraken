# ocrd_kraken

> OCR-D wrapper for the Kraken OCR engine

[![CI](https://github.com/OCR-D/ocrd_kraken/actions/workflows/ci.yml/badge.svg)](https://github.com/OCR-D/ocrd_kraken/actions/workflows/ci.yml)
[![Docker Automated build](https://img.shields.io/docker/automated/ocrd/kraken.svg)](https://hub.docker.com/r/ocrd/kraken/tags/)
[![image](https://circleci.com/gh/OCR-D/ocrd_kraken.svg?style=svg)](https://circleci.com/gh/OCR-D/ocrd_kraken)

## Introduction

This package offers [OCR-D](https://ocr-d.de/en/spec) compliant [workspace processors](https://ocr-d.de/en/spec/cli)
for (some of) the functionality of [Kraken](https://kraken.re).

(Each processor is a parameterizable step in a configurable [workflow](https://ocr-d.de/en/workflows)
of the [OCR-D functional model](https://ocr-d.de/en/about).
There are usually various alternative processor implementations for each step.
Data is represented with [METS](https://ocr-d.de/en/spec/mets) and [PAGE](https://ocr-d.de/en/spec/page).)

It includes image preprocessing (binarization), layout analysis (region and line+baseline segmentation), and text recognition.

## Installation

### With Docker

This is the best option if you want to run the software in a container.

You need to have [Docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/)


    docker pull ocrd/kraken


To run with Docker:


    docker run --rm \
    -v path/to/workspaces:/data \
    -v path/to/models:/usr/local/share/ocrd-resources \
    ocrd/kraken ocrd-kraken-recognize ...
    # or ocrd-kraken-segment or ocrd-kraken-binarize


### Native, from PyPI

This is the best option if you want to use the stable, released version.

    pip install ocrd_kraken


### Native, from git

Use this option if you want to change the source code or install the latest, unpublished changes.

We strongly recommend to use [venv](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/).

    git clone https://github.com/OCR-D/ocrd_kraken
    cd ocrd_kraken
    sudo make deps-ubuntu # or manually from git or via ocrd_all
    make deps        # or pip install -r requirements.txt
    make install     # or pip install .

## Models

Kraken uses data-driven (neural) models for segmentation and recognition, but comes with no pretrained "official" models.
There is a [public repository](https://zenodo.org/communities/ocr_models) of community-provided models, which can also
be queried and downloaded from via `kraken` standalone CLI.
(See [Kraken docs](https://kraken.re/master/advanced.html#repo) for details.)

For the OCR-D wrapper, since all OCR-D processors must resolve file/data resources in a [standardized way](https://ocr-d.de/en/spec/cli#processor-resources), there is a general mechanism for managing models, i.e. installing and using them by name. We currently manage our own list of recommended models (without delegating to the above repo).

Models always use the filename suffix `.mlmodel`, but are just loaded by their basename.

See the [OCR-D model guide](https://ocr-d.de/en/models) and

    ocrd resmgr --help

## Usage

For details, see docstrings in the individual processors and [ocrd-tool.json](ocrd_tesserocr/ocrd-tool.json) descriptions,
or simply `--help`.

Available [OCR-D processors](https://ocr-d.de/en/spec/cli) are:

- [ocrd-kraken-binarize](ocrd_kraken/binarize.py) (nlbin – not recommended)  
  - adds `AlternativeImage` files (per page, region or line) to the output fileGrp
- [ocrd-kraken-segment](ocrd_kraken/segment.py) (all-in-one segmentation – recommended for handwriting and simply layouted prints, or as pure line segmentation)  
  - adds `TextRegion`s to `Page` (if `level-of-operation=page`) or `TableRegion`s (if `table`)
  - adds `TextLine`s (with `Baseline`) to `TextRegion`s (for all `level-of-operation`)
  - masks existing segments during detection (unless `overwrite_segments`)
- [ocrd-kraken-recognize](ocrd_kraken/recognize.py) (benefits from annotated `Baseline`s, falls back to center-normalized bboxes)
  - adds `Word`s to `TextLine`s
  - adds `Glyph`s to `Word`s
  - adds `TextEquiv` (removing existing `TextEquiv` if `overwrite_text`)

## Testing

    make test


This downloads test data from https://github.com/OCR-D/assets under `repo/assets`, and runs some basic tests of the Python API.

Set `PYTEST_ARGS="-s --verbose"` to see log output (`-s`) and individual test results (`--verbose`).
