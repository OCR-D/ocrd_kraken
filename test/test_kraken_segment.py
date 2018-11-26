# pylint: disable=import-error

import os
import shutil

from test.base import TestCase, assets, main

from ocrd.resolver import Resolver
from ocrd_kraken.segment import KrakenSegment
PARAM_JSON = assets.url_of('param-segment.json')

WORKSPACE_DIR = '/tmp/ocrd-kraken-segment-test'

class TestKrakenSegment(TestCase):

    def setUp(self):
        if os.path.exists(WORKSPACE_DIR):
            shutil.rmtree(WORKSPACE_DIR)
        os.makedirs(WORKSPACE_DIR)

    def test_run1(self):
        resolver = Resolver()
        workspace = resolver.workspace_from_url(assets.url_of('kant_aufklaerung_1784-binarized/data/mets.xml'), dst_dir=WORKSPACE_DIR)
        proc = KrakenSegment(
            workspace,
            input_file_grp="OCR-D-IMG-BIN",
            output_file_grp="OCR-D-SEG-LINE-KRAKEN",
            parameter={'level-of-operation': 'line'}
        )
        proc.process()
        workspace.save_mets()

if __name__ == "__main__":
    main()
