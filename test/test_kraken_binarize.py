# pylint: disable=import-error

import os
import shutil

from test.base import TestCase, assets, main

from ocrd.resolver import Resolver
from ocrd import run_processor
from ocrd_kraken.binarize import KrakenBinarize
METS_HEROLD_SMALL = assets.url_of('SBB0000F29300010000/mets_one_file.xml')
PARAM_JSON = assets.url_of('param-binarize.json')

WORKSPACE_DIR = '/tmp/ocrd-kraken-binarize-test'

class TestKrakenBinarize(TestCase):

    def setUp(self):
        if os.path.exists(WORKSPACE_DIR):
            shutil.rmtree(WORKSPACE_DIR)
        os.makedirs(WORKSPACE_DIR)

    def test_param_json(self):
        resolver = Resolver(cache_enabled=True)
        workspace = resolver.workspace_from_url(METS_HEROLD_SMALL, directory=WORKSPACE_DIR)
        run_processor(
            KrakenBinarize,
            resolver=resolver,
            workspace=workspace,
            parameter=PARAM_JSON
        )

    def test_run1(self):
        resolver = Resolver(cache_enabled=True)
        workspace = resolver.workspace_from_url(assets.url_of('kant_aufklaerung_1784/mets.xml'), directory=WORKSPACE_DIR)
        proc = KrakenBinarize(
            workspace,
            input_file_grp="OCR-D-GT-PAGE",
            output_file_grp="OCR-D-IMG-BIN-KRAKEN",
            parameter={'level-of-operation': 'line'}
        )
        proc.process()
        workspace.save_mets()

if __name__ == "__main__":
    main()
