"""Test handling of apps."""

import pytest

from henson import Extension


def test_app_access_with_app(test_app):
    """Test that Extension.app returns the provided app."""
    extension = Extension(test_app)
    assert extension.app == test_app


def test_app_access_with_init_app(test_app):
    """Test that Extension.app returns an app set by init_app."""
    extension = Extension()
    extension.init_app(test_app)
    assert extension.app == test_app


def test_app_access_with_no_app_raises_runtimeerror():
    """Test that Extension.app raises RuntimeError when there is no app."""
    with pytest.raises(RuntimeError):
        Extension().app


def test_extension_without_default_settings(test_app):
    """Test that an Extension without DEFAULT_SETTINGS doesn't affect app."""
    class CustomExtension(Extension):
        pass

    CustomExtension(test_app)
    assert test_app.settings == {}


def test_extension_with_default_settings(test_app):
    """Test that an Extension's DEFAULT_SETTINGS populate an app's settings."""
    class CustomExtension(Extension):
        DEFAULT_SETTINGS = {'foo': 'bar'}

    CustomExtension(test_app)
    assert test_app.settings == {'foo': 'bar'}
