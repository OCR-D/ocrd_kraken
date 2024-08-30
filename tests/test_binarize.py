# pylint: disable=import-error

import json

from ocrd import run_processor
from ocrd_kraken.binarize import KrakenBinarize

from .assets import assets


PARAM_JSON = assets.url_of('param-binarize.json')

def test_param_json(workspace_sbb):
    run_processor(KrakenBinarize,
                  input_file_grp="OCR-D-IMG",
                  output_file_grp="OCR-D-BIN-KRAKEN",
                  parameter=json.load(open(PARAM_JSON)),
                  **workspace_sbb,
    )
    ws = workspace_sbb['workspace']
    ws.save_mets()

def test_binarize_regions(workspace_aufklaerung):
    run_processor(KrakenBinarize,
                  input_file_grp="OCR-D-GT-PAGE",
                  output_file_grp="OCR-D-BIN-KRAKEN",
                  parameter={'level-of-operation': 'region'},
                  **workspace_aufklaerung,
    )
    ws = workspace_aufklaerung['workspace']
    ws.save_mets()
    # FIXME: add result assertions (find_files, parsing PAGE etc)

def test_binarize_lines(workspace_aufklaerung):
    run_processor(KrakenBinarize,
                  input_file_grp="OCR-D-GT-PAGE",
                  output_file_grp="OCR-D-BIN-KRAKEN",
                  parameter={'level-of-operation': 'line'},
                  **workspace_aufklaerung,
    )
    ws = workspace_aufklaerung['workspace']
    ws.save_mets()
    # FIXME: add result assertions (find_files, parsing PAGE etc)
