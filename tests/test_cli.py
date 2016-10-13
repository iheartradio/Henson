"""CLI tests."""

from argparse import Namespace
from inspect import getsource

from argh import ArghParser, CommandError
import pytest


from henson import cli, Application


@pytest.fixture
def cli_kwargs():
    """Return keyword arguments for CLI actions."""
    # Use 1 for verbose to enable INFO logging.
    return {'quiet': False, 'verbose': 1}


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
        'def create_app(): return MockApplication()',
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


def test_applicationaction(good_mock_service):
    """Test _ApplicationAction."""
    action = cli._ApplicationAction(option_strings='a', dest='app')
    namespace = Namespace()
    action(None, namespace, 'good_import:app')
    assert isinstance(namespace.app, Application)


def test_import_application_only_module():
    """Test that _import_application fails with an invalid application_path."""
    with pytest.raises(CommandError) as e:
        cli._import_application('mymodule')
        assert 'Unable to find an import loader for mymodule' in e.message


def test_import_application_failed_loader():
    """Test that _import_application fails with a module that is not found."""
    with pytest.raises(CommandError) as e:
        cli._import_application('mymodule:app')
        assert 'Unable to find an import loader' in e.message


def test_import_application_failed_import(bad_mock_service):
    """Test that _import_application fails on dependency import errors."""
    with pytest.raises(ImportError):
        cli._import_application('bad_import:app')


def test_import_application_attribute_error():
    """Test that _import_application fails without an application attribute."""
    # NOTE: we don't need a real application here, just something that
    # doesn't have an attribute called `app`.
    with pytest.raises(AttributeError):
        cli._import_application('logging:app')


def test_import_application_non_henson_app():
    """Test that _import_application fails with the incorrect app type."""
    with pytest.raises(CommandError) as e:
        cli._import_application('logging:INFO')
        assert ("app must be an instance of a Henson application. Got "
                "<class 'int'>" in e.message)


def test_import_application_without_application():
    """Test that _import_applocation fails without an app name or instance."""
    with pytest.raises(CommandError) as e:
        cli._import_application('logging')
        assert 'No Henson application found' in e.message


def test_import_application_with_two_applications(double_mock_service):
    """Test that _import_application fails with ambiguous app choices."""
    with pytest.raises(CommandError) as e:
        cli._import_application('double_service')
        assert 'More than one Henson application found' in e.message


def test_import_application_app_autodetect(good_mock_service):
    """Test that an app can be selected automatically."""
    _, actual = cli._import_application('good_import')
    assert isinstance(actual, Application)


def test_import_application_callable(good_mock_service):
    """Test that an app can be loaded from a callable."""
    _, actual = cli._import_application('good_import:create_app')
    assert isinstance(actual, Application)


def test_import_application_explicit_app(good_mock_service):
    """Test that an app can be explicitly specified."""
    _, actual = cli._import_application('good_import:app')
    assert isinstance(actual, Application)


@pytest.mark.skip(reason='cli')
def test_register_commands(monkeypatch):
    """Test register_commands with no arguments."""
    monkeypatch.setattr(cli, 'parser', ArghParser('testing'))

    def simple():
        pass

    cli.register_commands('testing', [simple])

    args = cli.parser.parse_args(['testing', 'simple'])
    assert args


@pytest.mark.skip(reason='cli')
@pytest.mark.parametrize('arguments, a, b', (
    ([], 1, 2),
    (['2'], 2, 2),
    (['2', '3'], 2, 3),
))
def test_register_commands_keyword(monkeypatch, arguments, a, b):
    """Test register_commands with keyword arguments."""
    monkeypatch.setattr(cli, 'parser', ArghParser('testing'))

    def keyword(a=1, b=2):
        pass

    cli.register_commands('testing', [keyword])

    args = cli.parser.parse_args(['testing', 'keyword'] + arguments)
    assert args.a == a
    assert args.b == b


@pytest.mark.skip(reason='cli')
@pytest.mark.parametrize('arguments, first, second', (
    ([], 1, 2),
    (['--first', '2'], 2, 2),
    (['--second', '1'], 1, 1),
    (['--first', '2', '--second', '3'], 2, 3),
))
def test_register_commands_keyword_only(monkeypatch, arguments, first, second):
    """Test register_commands with keyword-only arguments."""
    monkeypatch.setattr(cli, 'parser', ArghParser('testing'))

    def keyword(*, first=1, second=2):
        pass

    cli.register_commands('testing', [keyword])

    args = cli.parser.parse_args(['testing', 'keyword'] + arguments)
    assert args.first == first
    assert args.second == second


@pytest.mark.skip(reason='cli')
def test_register_commands_keyword_only_conflicts(monkeypatch):
    """Test register_commands with key-only arguments with conflicts."""
    monkeypatch.setattr(cli, 'parser', ArghParser('testing'))

    def keyword(*, arg1=1, arg2=2):
        pass

    cli.register_commands('testing', [keyword])

    with pytest.raises(SystemExit):
        cli.parser.parse_args(['testing', 'keyword', '-a', '1'])


@pytest.mark.skip(reason='cli')
def test_register_commands_positional(monkeypatch):
    """Test register_commands with positional arguments."""
    monkeypatch.setattr(cli, 'parser', ArghParser('testing'))

    def positional(a, b):
        pass

    cli.register_commands('testing', [positional])

    args = cli.parser.parse_args(['testing', 'positional', '1', '2'])
    assert args.a == '1'
    assert args.b == '2'


@pytest.mark.parametrize('arguments, expected', (
    (['-q'], 1),
    (['-qq'], 2),
    (['--quiet'], 1),
    (['--quiet', '--quiet'], 2),
))
def test_register_commands_quiet(monkeypatch, arguments, expected):
    """Test that register_commands handles quiet."""
    monkeypatch.setattr(cli, 'parser', ArghParser('testing'))

    def verbosity(quiet):
        pass

    cli.register_commands('testing', [verbosity])

    args = cli.parser.parse_args(['testing', 'verbosity'] + arguments)
    assert args.quiet == expected


@pytest.mark.parametrize('arguments, quiet, verbose', (
    ('-q', 1, None),
    ('-qq', 2, None),
    ('-v', None, 1),
    ('-vv', None, 2),
))
def test_register_commands_quiet_and_verbose(monkeypatch, arguments, quiet,
                                             verbose):
    """Test that register_commands handles quiet and verbose."""
    monkeypatch.setattr(cli, 'parser', ArghParser('testing'))

    def verbosity(quiet, verbose):
        pass

    cli.register_commands('testing', [verbosity])

    args = cli.parser.parse_args(['testing', 'verbosity', arguments])
    assert args.quiet == quiet
    assert args.verbose == verbose


def test_register_commands_quiet_and_verbose_together_systemexit(monkeypatch):
    """Test that register_commands with quiet and verbose raises SystemExit."""
    monkeypatch.setattr(cli, 'parser', ArghParser('testing'))

    def verbosity(quiet, verbose):
        pass

    cli.register_commands('testing', [verbosity])

    with pytest.raises(SystemExit):
        cli.parser.parse_args(['testing', 'verbosity', '-q', '-v'])


@pytest.mark.parametrize('arguments, expected', (
    (['-v'], 1),
    (['-vv'], 2),
    (['--verbose'], 1),
    (['--verbose', '--verbose'], 2),
))
def test_register_commands_verbose(monkeypatch, arguments, expected):
    """Test that register_commands handles quiet."""
    monkeypatch.setattr(cli, 'parser', ArghParser('testing'))

    def verbosity(verbose):
        pass

    cli.register_commands('testing', [verbosity])

    args = cli.parser.parse_args(['testing', 'verbosity'] + arguments)
    assert args.verbose == expected


@pytest.mark.skip(reason='cli')
def test_run_forever(good_mock_service, cli_kwargs, caplog, capsys):
    """Test that run_forever is called on the imported app."""
    cli.run('good_import:app', **cli_kwargs)
    out, _ = capsys.readouterr()
    assert 'Running <Application: testing> forever' in caplog.text()
    assert 'Run, Forrest, run!' in out


@pytest.mark.skip(reason='cli')
def test_run_with_reloader(good_mock_service, cli_kwargs, caplog, capsys):
    """Test that an app is run with the reloader."""
    cli.run('good_import:app', reloader=True, **cli_kwargs)
    out, _ = capsys.readouterr()
    assert 'Running <Application: testing> with reloader' in caplog.text()
    assert 'Run, Forrest, run!' in out
