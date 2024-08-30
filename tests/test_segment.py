# pylint: disable=import-error

from ocrd import run_processor
from ocrd_kraken.segment import KrakenSegment


def test_run_blla(workspace_manifesto):
    run_processor(KrakenSegment,
                  input_file_grp="OCR-D-IMG-BIN",
                  output_file_grp="OCR-D-SEG-LINE-KRAKEN",
                  parameter={'maxcolseps': 0, 'use_legacy': False},
                  **workspace_manifesto,
    )
    ws = workspace_manifesto['workspace']
    ws.save_mets()
    # FIXME: add result assertions (find_files, parsing PAGE etc)

def test_run_blla_regionlevel(workspace_aufklaerung_region):
    run_processor(KrakenSegment,
                  input_file_grp="OCR-D-GT-SEG-REGION",
                  output_file_grp="OCR-D-SEG-LINE-KRAKEN",
                  page_id="phys_0005",
                  parameter={'maxcolseps': 0, 'use_legacy': False},
                  **workspace_aufklaerung_region,
    )
    ws = workspace_aufklaerung_region['workspace']
    ws.save_mets()
    # FIXME: add result assertions (find_files, parsing PAGE etc)

def test_run_legacy(workspace_manifesto):
    run_processor(KrakenSegment,
                  input_file_grp="OCR-D-IMG-BIN",
                  output_file_grp="OCR-D-SEG-LINE-KRAKEN",
                  parameter={'maxcolseps': 0, 'use_legacy': True},
                  **workspace_manifesto,
    )
    ws = workspace_manifesto['workspace']
    ws.save_mets()
    # FIXME: add result assertions (find_files, parsing PAGE etc)
