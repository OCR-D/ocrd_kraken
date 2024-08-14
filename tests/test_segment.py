# pylint: disable=import-error

import os
import shutil

from tests.base import TestCase, assets, main

from ocrd import Resolver, run_processor
from ocrd_utils import initLogging, pushd_popd
from ocrd_kraken.segment import KrakenSegment

class TestKrakenSegment(TestCase):

    def setUp(self):
        initLogging()

    def test_run_blla(self):
        resolver = Resolver()
        with pushd_popd(tempdir=True) as tempdir:
            workspace = resolver.workspace_from_url(assets.path_to('communist_manifesto/data/mets.xml'), dst_dir=tempdir, download=True)
            run_processor(
                KrakenSegment,
                workspace=workspace,
                input_file_grp="OCR-D-IMG-BIN",
                output_file_grp="OCR-D-SEG-LINE-KRAKEN",
                parameter={'maxcolseps': 0, 'use_legacy': False}
            )
            workspace.save_mets()
            # FIXME: add result assertions (find_files, parsing PAGE etc)

    def test_run_blla_regionlevel(self):
        resolver = Resolver()
        with pushd_popd(tempdir=True) as tempdir:
            workspace = resolver.workspace_from_url(assets.path_to('kant_aufklaerung_1784-page-region/data/mets.xml'), dst_dir=tempdir, download=True)
            run_processor(
                KrakenSegment,
                workspace=workspace,
                input_file_grp="OCR-D-GT-SEG-REGION",
                output_file_grp="OCR-D-SEG-LINE-KRAKEN",
                page_id="phys_0005",
                parameter={'maxcolseps': 0, 'use_legacy': False}
            )
            workspace.save_mets()
            # FIXME: add result assertions (find_files, parsing PAGE etc)

    def test_run_legacy(self):
        resolver = Resolver()
        # with pushd_popd('/tmp/kraken-test') as tempdir:
        with pushd_popd(tempdir=True) as tempdir:
            workspace = resolver.workspace_from_url(assets.path_to('communist_manifesto/data/mets.xml'), dst_dir=tempdir, download=True)
            run_processor(
                KrakenSegment,
                workspace=workspace,
                input_file_grp="OCR-D-IMG-BIN",
                output_file_grp="OCR-D-SEG-LINE-KRAKEN",
                parameter={'maxcolseps': 0, 'use_legacy': True}
            )
            workspace.save_mets()
            # FIXME: add result assertions (find_files, parsing PAGE etc)

if __name__ == "__main__":
    main(__file__)
