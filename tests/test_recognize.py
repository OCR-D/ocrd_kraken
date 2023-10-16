# pylint: disable=import-error

import os
import shutil

from tests.base import TestCase, assets, main

from ocrd import Resolver, run_processor
from ocrd_utils import initLogging, pushd_popd
from ocrd_kraken.recognize import KrakenRecognize

class TestKrakenRecognize(TestCase):

    def setUp(self):
        initLogging()

    def test_recognize(self):
        resolver = Resolver()
        # with pushd_popd('/tmp/kraken-test') as tempdir:
        with pushd_popd(tempdir=True) as tempdir:
            workspace = resolver.workspace_from_url(assets.path_to('communist_manifesto/data/mets.xml'), dst_dir=tempdir, download=True)
            workspace.overwrite_mode = True
            proc = KrakenRecognize(
                workspace,
                input_file_grp="OCR-D-SEG-KRAKEN",
                output_file_grp="OCR-D-OCR-KRAKEN",
            )
            proc.process()
            workspace.save_mets()

if __name__ == "__main__":
    main(__file__)
