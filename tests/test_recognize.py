# pylint: disable=import-error

from ocrd import run_processor
from ocrd_kraken.recognize import KrakenRecognize
from ocrd_kraken.binarize import KrakenBinarize


def test_recognize(workspace_aufklaerung):
    # some models (like default en) require binarized images
    run_processor(KrakenBinarize,
                  input_file_grp="OCR-D-GT-PAGE",
                  output_file_grp="OCR-D-GT-PAGE-BIN",
                  **workspace_aufklaerung,
    )
    run_processor(KrakenRecognize,
                  # re-use layout, overwrite text:
                  input_file_grp="OCR-D-GT-PAGE-BIN",
                  output_file_grp="OCR-D-OCR-KRAKEN",
                  parameter={'overwrite_text': True},
                  **workspace_aufklaerung,
    )
    ws = workspace_aufklaerung['workspace']
    ws.save_mets()
    # FIXME: add result assertions (find_files, parsing PAGE etc)
