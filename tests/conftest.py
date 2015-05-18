"""Test the application registry."""

import pytest

from henson.registry import Registry


@pytest.fixture
def modules_tmpdir(tmpdir, monkeypatch):
    """Add a temporary directory for modules to sys.path."""
    tmp = tmpdir.mkdir('tmp_modules')
    monkeypatch.syspath_prepend(str(tmp))
    return tmp


@pytest.fixture
def mock_service(modules_tmpdir):
    """Create a package for a fake service."""
    service = modules_tmpdir.mkdir('mock_service')
    service.join('settings.py').write('SERVICE_SETTING = 1')
    service.join('process.py').write('def run(app, message): return message')

    # Add a couple of other modules that can be used for testing errors.
    service.join('bad_import.py').write('import not_a_real_module')
    service.join('type_error.py').write('1 + "a"')


@pytest.fixture
def registry():
    """Create an application registry."""
    return Registry()


@pytest.fixture
def settings():
    """Create a configuration object."""
    class Config:
        A = 1
        B = 2

    return Config
