# pylint: disable=import-error

import os
import shutil

from test.base import TestCase, assets, main

from ocrd.resolver import Resolver
from ocrd import run_processor
from ocrd_kraken import KrakenOcr, KrakenBinarize, KrakenSegment

WORKSPACE_DIR = '/tmp/ocrd-kraken-ocr-test'

class TestKrakenOcr(TestCase):

    def setUp(self):
        if os.path.exists(WORKSPACE_DIR):
            shutil.rmtree(WORKSPACE_DIR)
        os.makedirs(WORKSPACE_DIR)

    def test_param_json(self):
        resolver = Resolver()
        workspace = resolver.workspace_from_url(assets.url_of('SBB0000F29300010000/data/mets_one_file.xml'), dst_dir=WORKSPACE_DIR)
        run_processor(
            KrakenBinarize,
            resolver=resolver,
            workspace=workspace,
            input_file_grp="INPUT",
            output_file_grp="OCR-D-IMG-BIN-KRAKEN"
        )
        workspace.save_mets()

if __name__ == "__main__":
    main()
