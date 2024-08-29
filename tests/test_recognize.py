# pylint: disable=import-error

from tests.base import *

from ocrd import run_processor
from ocrd_kraken.recognize import KrakenRecognize

def test_recognize(workspace_manifesto):
    ws = workspace_manifesto
    print(ws)
    print(type(ws))
    print(ws.directory)
    run_processor(KrakenRecognize,
                  workspace=ws,
                  input_file_grp="OCR-D-SEG-KRAKEN",
                  output_file_grp="OCR-D-OCR-KRAKEN",
    )
    ws.save_mets()
    # FIXME: add result assertions (find_files, parsing PAGE etc)
