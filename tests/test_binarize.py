# pylint: disable=import-error

import json
import os

from ocrd import run_processor
from ocrd_utils import MIMETYPE_PAGE
from ocrd_models.constants import NAMESPACES
from ocrd_modelfactory import page_from_file

from ocrd_kraken.binarize import KrakenBinarize

from .assets import assets


PARAM_JSON = assets.url_of('param-binarize.json')

def analyse_result(ws, level):
    assert os.path.isdir(os.path.join(ws.directory, 'OCR-D-BIN-KRAKEN'))
    out_files = list(ws.find_files(fileGrp="OCR-D-BIN-KRAKEN", mimetype=MIMETYPE_PAGE))
    assert len(out_files), "found no output PAGE file"
    out_images = list(ws.find_files(fileGrp="OCR-D-BIN-KRAKEN", mimetype="//^image/.*"))
    assert len(out_images), "found no output image file"
    out_pcgts = page_from_file(out_files[0])
    assert out_pcgts is not None
    out_images = out_pcgts.etree.xpath('//page:%s/page:AlternativeImage[contains(@comments,"binarized")]' % level, namespaces=NAMESPACES)
    assert len(out_images) > 0, "found no binarized AlternativeImages in output PAGE file"

def test_param_json(workspace_sbb):
    run_processor(KrakenBinarize,
                  input_file_grp="OCR-D-IMG",
                  output_file_grp="OCR-D-BIN-KRAKEN",
                  parameter=json.load(open(PARAM_JSON)),
                  **workspace_sbb,
    )
    ws = workspace_sbb['workspace']
    ws.save_mets()
    analyse_result(ws, 'Page')

def test_binarize_regions(workspace_aufklaerung):
    run_processor(KrakenBinarize,
                  input_file_grp="OCR-D-GT-PAGE",
                  output_file_grp="OCR-D-BIN-KRAKEN",
                  parameter={'level-of-operation': 'region'},
                  **workspace_aufklaerung,
    )
    ws = workspace_aufklaerung['workspace']
    ws.save_mets()
    analyse_result(ws, 'TextRegion')

def test_binarize_lines(workspace_aufklaerung):
    run_processor(KrakenBinarize,
                  input_file_grp="OCR-D-GT-PAGE",
                  output_file_grp="OCR-D-BIN-KRAKEN",
                  parameter={'level-of-operation': 'line'},
                  **workspace_aufklaerung,
    )
    ws = workspace_aufklaerung['workspace']
    ws.save_mets()
    analyse_result(ws, 'TextLine')

