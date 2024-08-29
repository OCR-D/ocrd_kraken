# pylint: disable=unused-import

from multiprocessing import Process
from time import sleep
import pytest

from ocrd import Resolver, Workspace, OcrdMetsServer
from ocrd_utils import pushd_popd, disableLogging, initLogging, setOverrideLogLevel, config

from .assets import assets

@pytest.fixture
def workspace(tmpdir, pytestconfig):
    def _make_workspace(workspace_path):
        initLogging()
        if pytestconfig.getoption('verbose') > 0:
            setOverrideLogLevel('DEBUG')
        with pushd_popd(tmpdir):
            yield Resolver().workspace_from_url(workspace_path, dst_dir=tmpdir, download=True)
    return _make_workspace

@pytest.fixture
def workspace_manifesto(workspace):
    yield from workspace(assets.path_to('communist_manifesto/data/mets.xml'))

@pytest.fixture
def workspace_aufklaerung(workspace):
    yield from workspace(assets.path_to('kant_aufklaerung_1784/data/mets.xml'))

@pytest.fixture
def workspace_aufklaerung_region(workspace):
    yield from workspace(assets.path_to('kant_aufklaerung_1784-page-region/data/mets.xml'))

@pytest.fixture
def workspace_sbb(workspace):
    yield from workspace(assets.url_of('SBB0000F29300010000/data/mets_one_file.xml'))

