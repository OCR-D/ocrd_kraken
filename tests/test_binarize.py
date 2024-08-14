# pylint: disable=import-error

import os
import shutil
import pytest

from tests.base import assets, main

from ocrd import Resolver, run_processor
from ocrd_kraken.binarize import KrakenBinarize
from ocrd_utils.logging import setOverrideLogLevel

setOverrideLogLevel('DEBUG')

PARAM_JSON = assets.url_of('param-binarize.json')


@pytest.fixture()
def workspace(tmpdir):
    if os.path.exists(tmpdir):
        shutil.rmtree(tmpdir)
    workspace = Resolver().workspace_from_url(
        assets.path_to('kant_aufklaerung_1784/data/mets.xml'),
        dst_dir=tmpdir,
        download=True
    )
    return workspace


#  def test_param_json(self):
#      workspace =  resolver.workspace_from_url(assets.url_of('SBB0000F29300010000/data/mets_one_file.xml'), dst_dir=WORKSPACE_DIR)
#      run_processor(
#          KrakenBinarize,
#          resolver=resolver,
#          workspace=workspace,
#          parameter=PARAM_JSON
#      )

def test_binarize_regions(workspace):
    run_processor(KrakenBinarize,
                  workspace=workspace,
                  input_file_grp="OCR-D-GT-PAGE",
                  output_file_grp="OCR-D-IMG-BIN-KRAKEN",
                  parameter={'level-of-operation': 'region'}
    )
    workspace.save_mets()
    # FIXME: add result assertions (find_files, parsing PAGE etc)

def test_binarize_lines(workspace):
    run_processor(KrakenBinarize,
                  workspace=workspace,
                  input_file_grp="OCR-D-GT-PAGE",
                  output_file_grp="OCR-D-IMG-BIN-KRAKEN",
                  parameter={'level-of-operation': 'line'}
    )
    workspace.save_mets()
    # FIXME: add result assertions (find_files, parsing PAGE etc)

if __name__ == "__main__":
    main(__file__)
