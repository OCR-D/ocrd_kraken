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

    def test_run_blla(self):
        resolver = Resolver()
        with pushd_popd(tempdir=True) as tempdir:
            workspace = resolver.workspace_from_url(assets.path_to('communist_manifesto/data/mets.xml'), dst_dir=tempdir, download=True)
            proc = KrakenSegment(
                workspace,
                input_file_grp="OCR-D-IMG-BIN",
                output_file_grp="OCR-D-SEG-LINE-KRAKEN",
                parameter={'maxcolseps': 0, 'use_legacy': False}
            )
            proc.process()
            workspace.save_mets()

    def test_run_legacy(self):
        resolver = Resolver()
        # with pushd_popd('/tmp/kraken-test') as tempdir:
        with pushd_popd(tempdir=True) as tempdir:
            workspace = resolver.workspace_from_url(assets.path_to('communist_manifesto/data/mets.xml'), dst_dir=tempdir, download=True)
            proc = KrakenSegment(
                workspace,
                input_file_grp="OCR-D-IMG-BIN",
                output_file_grp="OCR-D-SEG-LINE-KRAKEN",
                parameter={'maxcolseps': 0, 'use_legacy': True}
            )
            proc.process()
            workspace.save_mets()

if __name__ == "__main__":
    main(__file__)
