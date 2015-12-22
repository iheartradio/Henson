"""CLI tests."""

from inspect import getsource

from argh import CommandError
import pytest


from henson.cli import run


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
def good_mock_service(modules_tmpdir, test_app):
    """Create a module for a fake service."""
    good_import = modules_tmpdir.join('good_import.py')
    good_import.write('\n'.join((
        'from henson import Application',
        getsource(type(test_app)),
        'app = MockApplication()',
    )))


@pytest.fixture
def double_mock_service(modules_tmpdir, test_app):
    """Create a module with two fake services."""
    double_service = modules_tmpdir.join('double_service.py')
    double_service.write('\n'.join((
        'from henson import Application',
        getsource(type(test_app)),
        'app1 = MockApplication()',
        'app2 = MockApplication()',
    )))


def test_run_only_module():
    """Test that the run command fails with a malformed application_path."""
    with pytest.raises(CommandError) as e:
        run('mymodule')
        assert 'Unable to find an import loader for mymodule' in e.message


def test_run_failed_loader():
    """Test that the run command fails with a module that is not found."""
    with pytest.raises(CommandError) as e:
        run('mymodule:app')
        assert 'Unable to find an import loader' in e.message


def test_run_failed_import(bad_mock_service):
    """Test that the run command fails on dependency import errors."""
    with pytest.raises(ImportError):
        run('bad_import:app')


def test_run_attribute_error():
    """Test that the run command fails without an application attribute."""
    # NOTE: we don't need a real application here, just something that
    # doesn't have an attribute called `app`.
    with pytest.raises(AttributeError):
        run('logging:app')


def test_run_non_henson_app():
    """Test that the run command fails with the incorrect app type."""
    with pytest.raises(CommandError) as e:
        run('logging:INFO')
        assert ("app must be an instance of a Henson application. Got "
                "<class 'int'>" in e.message)


def test_run_without_application():
    """Test that the run command fails without an app name or instance."""
    with pytest.raises(CommandError) as e:
        run('logging')
        assert 'No Henson application found' in e.message


def test_run_with_two_applications(double_mock_service):
    """Test that the run command fails with ambiguous app choices."""
    with pytest.raises(CommandError) as e:
        run('double_service')
        assert 'More than one Henson application found' in e.message


def test_run_app_autodetect(good_mock_service, capsys):
    """Test that an app can be selected automatically."""
    run('good_import')
    out, _ = capsys.readouterr()
    assert 'Run, Forrest, run!' in out


def test_run_forever(good_mock_service, capsys):
    """Test that run_forever is called on the imported app."""
    run('good_import:app')
    out, _ = capsys.readouterr()
    assert 'Run, Forrest, run!' in out
