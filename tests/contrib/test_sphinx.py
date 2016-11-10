"""Tests for henson.contrib.sphinx."""

from docutils.statemachine import StringList
import pytest

from henson import Extension
from henson.contrib import sphinx


@pytest.fixture
def modules_tmpdir(tmpdir, monkeypatch):
    """Add a temporary directory for modules to sys.path."""
    tmp = tmpdir.mkdir('tmp_modules')
    monkeypatch.syspath_prepend(str(tmp))
    return tmp


@pytest.fixture
def test_module(modules_tmpdir, test_app):
    """Create a module for a fake extension."""
    fake_extension = modules_tmpdir.join('fake_extension.py')
    fake_extension.write('\n'.join((
        'from henson import Extension',
        'class FakeExtension(Extension):',
        '    def register_cli(self): pass',
    )))


@pytest.fixture
def test_directive(test_module):
    """Return an instance of HensonCLIDirective."""
    return sphinx.HensonCLIDirective(
        name='hensoncli',
        arguments=['fake_extension:FakeExtension'],
        options={},
        content=StringList([], items=[]),
        lineno=1,
        content_offset=0,
        block_text='.. hensoncli:: fake_extension:FakeExtension\n',
        state=None,
        state_machine=None,
    )


def test_hensoncliextensiondirective_sets_parser(test_directive):
    """Test that HensonCLIDirective.prepare_autoprogram sets the parser."""
    test_directive.prepare_autoprogram()
    assert test_directive.arguments == ('henson.cli:parser',)


def test_hensoncliextentiondirective_register_cli(test_directive):
    """Test that HensonCLIDirective.register_cli doesn't fail."""
    # This will only test that it runs without raising an exception.
    test_directive.register_cli()


def test_import_extension(test_module):
    """Test that _import_extension returns the extension."""
    import_path = 'fake_extension:FakeExtension'
    extension = sphinx._import_extension(import_path)
    assert issubclass(extension, Extension)


def test_setup():
    """Test that setup registers the directive."""
    class SphinxApplication:
        def add_directive(self, directive, cls):
            self.directive = directive
            self.cls = cls

    app = SphinxApplication()

    sphinx.setup(app)

    assert app.directive == 'hensoncli'
    assert app.cls is sphinx.HensonCLIDirective
