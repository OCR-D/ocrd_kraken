Change Log
==========

Versioned according to [Semantic Versioning](http://semver.org/).

## Unreleased

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
[0.2.0]: v0.2.0...v0.1.2
[0.1.2]: v0.1.2...v0.1.1
[0.1.1]: v0.1.1...v0.1.0
[0.1.0]: v0.1.0...v0.0.2
[0.0.2]: v0.0.2...v0.0.1
[0.0.1]: ../../compare/HEAD...v0.0.1
