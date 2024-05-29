Change Log
==========

Versioned according to [Semantic Versioning](http://semver.org/).

## Unreleased

## [0.4.1] - 2024-05-29

Fixed:

  * recognize: improve baseline/polgon robustness

Changed:

  * segment/recognize: adapt and bump to Kraken v5
  * adapt to Python importlib instead of pkg_resources
  * update tests/CI

## [0.4.0] - 2024-02-11

Fixed:

  * binarize: OCR-D conformity (PAGE output, AlternativeImage input/output)
  * docstrings

Added:

  * recognize: param `overwrite_text`
  * segment: param `overwrite_segments`
  * segment: param `level-of-operation` (now supports `table` and `region`, too)

Changed:

  * binarize: :fire: renamed `level-of-operation=block` to `region`
  * segment: existing segmentation will be masked away (unless `overwrite_segments`)

## [0.3.1] - 2023-08-17

Fixed:

  * recognize: only apply `one_channel_mode` (whether to use `binarized` input)
    if the model has only one input channel
  * recognize: project text results to region level in order
  * recognize: iterate line results via proper word splitting
  * recognize: add proper line and word confidences
  * recognize: avoid invalid polygons on single-glyph words
  * recognize: workaround for better quality box cuts
  * recognize: workaround for empty/failed line records
  * segment: update blla.model URL (master→main)

Changed:

  * recognize: pass lines in baseline format if any baselines are annotated
  * recognize: ensure baselines are valid and consistent with line polygon
  * recognize/segment: fall back to CPU if CUDA not available

## [0.3.0] - 2022-10-23

Fixed:

  * recognize: clip bounding boxes to canvas
  * Updated README to reflect current capabilities
  * Docker build working and with proper tagging

Added:

  * `resources` in `ocrd-tool.json` for the OCR-D resource manager

## [0.2.0] - 2022-07-18

Added:

  * text recognition with `ocrd-kraken-recognize`, #33
  * rewrite of `ocrd-kraken-segment`, #33

## [0.1.2] - 2020-09-24

Fixed:

  * Logging according to https://github.com/OCR-D/core/pull/599

## [0.1.1] - 2019-10-21

Fixed:

  * Pass `pageId` to workspace.add_file, #28
  * Updated Dockerfile

## [0.1.0] - 2018-07-03

Fixed:

  * Adapted to 1.0.0 core API

Added:

  * input/output file groups to ocrd-tool.json

## [0.0.2] - 2018-07-03

Fixed:

  * Non-destructively set defaults for input and output groups

Changed:

  * Update version requirement for kraken, core, etc.

## [0.0.1] - 2018-07-03

Initial release

<!-- link-labels -->
[0.4.1]: v0.4.1...v0.4.0
[0.4.0]: v0.4.0...v0.3.1
[0.3.1]: v0.3.1...v0.3.0
[0.3.0]: v0.3.0...v0.2.0
[0.2.0]: v0.2.0...v0.1.2
[0.1.2]: v0.1.2...v0.1.1
[0.1.1]: v0.1.1...v0.1.0
[0.1.0]: v0.1.0...v0.0.2
[0.0.2]: v0.0.2...v0.0.1
[0.0.1]: ../../compare/HEAD...v0.0.1
