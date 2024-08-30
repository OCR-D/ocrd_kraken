# pylint: disable=import-error

import os

from ocrd import run_processor
from ocrd_utils import MIMETYPE_PAGE
from ocrd_models.constants import NAMESPACES
from ocrd_modelfactory import page_from_file

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
    assert os.path.isdir(os.path.join(ws.directory, 'OCR-D-OCR-KRAKEN'))
    results = ws.find_files(file_grp='OCR-D-OCR-KRAKEN', mimetype=MIMETYPE_PAGE)
    result0 = next(results, False)
    assert result0, "found no output PAGE file"
    result0 = page_from_file(result0)
    text0 = result0.etree.xpath('//page:Glyph/page:TextEquiv/page:Unicode', namespaces=NAMESPACES)
    assert len(text0) > 0, "found no glyph text in output PAGE file"
