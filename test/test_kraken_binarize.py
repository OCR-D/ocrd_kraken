# pylint: disable=import-error

from test.base import TestCase, assets, main

from ocrd.resolver import Resolver
from ocrd_kraken.binarize import KrakenBinarize
METS_HEROLD_SMALL = assets.url_of('SBB0000F29300010000/mets_one_file.xml')

WORKSPACE_DIR = '/tmp/ocrd-kraken-binarize-test'

class TestKrakenBinarize(TestCase):

    def runTest(self):
        resolver = Resolver(cache_enabled=True)
        workspace = resolver.workspace_from_url(METS_HEROLD_SMALL, directory=WORKSPACE_DIR)
        KrakenBinarize(workspace, input_filegrp="INPUT", output_filegrp="OCR-D-SEG-BLOCK").process()

if __name__ == "__main__":
    main()
