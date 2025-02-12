# pylint: disable=import-error

import os

from ocrd import run_processor
from ocrd_utils import MIMETYPE_PAGE
from ocrd_models.constants import NAMESPACES
from ocrd_modelfactory import page_from_file

from ocrd_kraken.segment import KrakenSegment
from ocrd_kraken.binarize import KrakenBinarize


def analyse_result(ws):
    assert os.path.isdir(os.path.join(ws.directory, 'OCR-D-SEG-LINE-KRAKEN'))
    out_files = list(ws.find_files(fileGrp="OCR-D-SEG-LINE-KRAKEN", mimetype=MIMETYPE_PAGE))
    assert len(out_files), "found no output PAGE file"
    out_pcgts = page_from_file(out_files[0])
    assert out_pcgts is not None
    out_regions = out_pcgts.etree.xpath('//page:TextRegion/page:Coords', namespaces=NAMESPACES)
    assert len(out_regions) > 0, "found no text regions in output PAGE file"
    out_lines = out_pcgts.get_Page().get_AllTextLines()
    assert len(out_lines), "found no text lines in output PAGE file"

def test_run_blla(workspace_aufklaerung):
    run_processor(KrakenSegment,
                  input_file_grp="OCR-D-IMG",
                  output_file_grp="OCR-D-SEG-LINE-KRAKEN",
                  parameter={'maxcolseps': 0, 'use_legacy': False},
                  **workspace_aufklaerung,
    )
    ws = workspace_aufklaerung['workspace']
    ws.save_mets()
    analyse_result(ws)

def test_run_blla_regionlevel(workspace_aufklaerung_region):
    run_processor(KrakenSegment,
                  input_file_grp="OCR-D-GT-SEG-REGION",
                  output_file_grp="OCR-D-SEG-LINE-KRAKEN",
                  # only 1 page (takes 3min per page without GPU)
                  page_id="phys_0005",
                  parameter={'maxcolseps': 0, 'use_legacy': False},
                  **workspace_aufklaerung_region,
    )
    ws = workspace_aufklaerung_region['workspace']
    ws.save_mets()
    analyse_result(ws)

def test_run_legacy(workspace_aufklaerung):
    # legacy segmentation requires binarized images
    run_processor(KrakenBinarize,
                  input_file_grp="OCR-D-GT-PAGE",
                  output_file_grp="OCR-D-GT-PAGE-BIN",
                  **workspace_aufklaerung,
    )
    run_processor(KrakenSegment,
                  # overwrite layout:
                  input_file_grp="OCR-D-GT-PAGE-BIN",
                  output_file_grp="OCR-D-SEG-LINE-KRAKEN",
                  parameter={'maxcolseps': 0, 'use_legacy': True, 'overwrite_segments': True},
                  **workspace_aufklaerung,
    )
    ws = workspace_aufklaerung['workspace']
    ws.save_mets()
    analyse_result(ws)
