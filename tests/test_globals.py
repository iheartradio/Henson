import pytest

from henson import Application, globals as globals_


def test_current_application(mock_registry):
    """Test that current_application is an Application."""
    app = Application('testing')
    assert app == globals_.current_application


def test_current_application_runtimeerror():
    """Test that accessing current application raises RuntimeError."""
    with pytest.raises(RuntimeError):
        globals_.current_application.settings
