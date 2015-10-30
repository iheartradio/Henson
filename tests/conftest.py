"""Test the application registry."""

import asyncio
from inspect import getsource

from click.testing import CliRunner
import pytest

from henson import Application


class MockApplication(Application):
    """A stub application that can be used for testing.

    Args:
        **settings: Keyword arguments that will be used as settings.
    """

    def __init__(self, **settings):
        """Initialize the instance."""
        self.name = 'testing'
        self.settings = settings

        self.error_callbacks = []

    def run_forever(self):
        print('Run, Forrest, run!')


class MockConsumer:
    """A stub consumer that can be used for testing."""

    @asyncio.coroutine
    def read(self):
        """Return an item."""
        return 1


@pytest.fixture
def callback():
    """Return a stubbed callback function."""
    def _inner(*args):
        pass
    return _inner


@pytest.fixture
def coroutine():
    """Return a coroutine function."""
    @asyncio.coroutine
    def _inner(*args, **kwargs):
        pass
    return _inner


@pytest.fixture
def settings():
    """Create a configuration object."""
    class Config:
        A = 1
        B = 2

    return Config


@pytest.fixture
def test_app():
    """Return a test application."""
    return MockApplication()


@pytest.fixture
def test_consumer():
    """Return a test consumer."""
    return MockConsumer()


@pytest.fixture
def click_runner():
    """Return a click CLI runner."""
    return CliRunner()


@pytest.fixture
def modules_tmpdir(tmpdir, monkeypatch):
    """Add a temporary directory for modules to sys.path."""
    tmp = tmpdir.mkdir('tmp_modules')
    monkeypatch.syspath_prepend(str(tmp))
    return tmp


@pytest.fixture
def bad_mock_service(modules_tmpdir):
    """Create a module for a fake service that cannot be imported."""
    modules_tmpdir.join('bad_import.py').write('import not_a_real_module')


@pytest.fixture
def good_mock_service(modules_tmpdir):
    """Create a module for a fake service."""
    good_import = modules_tmpdir.join('good_import.py')
    good_import.write('\n'.join((
        'from henson import Application',
        getsource(MockApplication),
        'app = MockApplication()',
    )))


@pytest.fixture
def double_mock_service(modules_tmpdir):
    """Create a module with two fake services."""
    double_service = modules_tmpdir.join('double_service.py')
    double_service.write('\n'.join((
        'from henson import Application',
        getsource(MockApplication),
        'app1 = MockApplication()',
        'app2 = MockApplication()',
    )))
