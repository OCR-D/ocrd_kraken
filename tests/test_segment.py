# pylint: disable=import-error

from ocrd import run_processor
from ocrd_kraken.segment import KrakenSegment
from ocrd_kraken.binarize import KrakenBinarize


def test_run_blla(workspace_aufklaerung):
    run_processor(KrakenSegment,
                  input_file_grp="OCR-D-IMG",
                  output_file_grp="OCR-D-SEG-LINE-KRAKEN",
                  parameter={'maxcolseps': 0, 'use_legacy': False},
                  **workspace_aufklaerung,
    )
    ws = workspace_aufklaerung['workspace']
    ws.save_mets()
    # FIXME: add result assertions (find_files, parsing PAGE etc)

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
    # FIXME: add result assertions (find_files, parsing PAGE etc)

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
    # FIXME: add result assertions (find_files, parsing PAGE etc)
