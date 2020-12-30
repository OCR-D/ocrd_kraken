# pylint: disable=import-error

import os
import shutil

from tests.base import TestCase, assets, main

from ocrd import Resolver
from ocrd_utils import initLogging, pushd_popd
from ocrd_kraken.segment import KrakenSegment

class TestKrakenSegment(TestCase):

    def setUp(self):
        initLogging()

    def test_run1(self):
        resolver = Resolver()
        with pushd_popd(tempdir=True) as tempdir:
        # with pushd_popd('/tmp/kraken-test') as tempdir:
            workspace = resolver.workspace_from_url(assets.path_to('communist_manifesto/data/mets.xml'), dst_dir=tempdir)
            proc = KrakenSegment(
                workspace,
                input_file_grp="OCR-D-IMG-BIN",
                output_file_grp="OCR-D-SEG-LINE-KRAKEN"
            )
            proc.process()
            workspace.save_mets()
            assert 0

if __name__ == "__main__":
    main(__file__)
