"""CLI tests."""

import pytest  # noqa

from henson.cli import cli, run


def test_entry_point(click_runner):
    """Test that the CLI entry point prints the help menu."""
    result = click_runner.invoke(cli)
    assert result.exit_code == 0
    assert 'Commands:' in result.output


def test_run_without_app_path(click_runner):
    """Test that the run command fails without an application_path."""
    result = click_runner.invoke(run)
    assert result.exit_code != 0
    assert 'Error: Missing argument "application_path".' in result.output


def test_run_only_module(click_runner):
    """Test that the run command fails with a malformed application_path."""
    result = click_runner.invoke(run, ['mymodule'])
    assert result.exit_code != 0
    assert ('Error: application_path must be of the form '
            'path.to.module:application_name' in result.output)


def test_run_failed_loader(click_runner):
    """Test that the run command fails with a module that is not found."""
    result = click_runner.invoke(run, ['mymodule:app'])
    assert result.exit_code != 0
    assert 'Error: Unable to find an import loader' in result.output


def test_run_failed_import(click_runner, bad_mock_service):
    """Test that the run command fails on dependency import errors."""
    result = click_runner.invoke(run, ['bad_import:app'])
    assert result.exit_code != 0
    assert 'Error: Unable to import bad_import' in result.output


def test_run_attribute_error(click_runner):
    """Tests that the run command fails without an application attribute."""
    # NOTE: we don't need a real application here, just something that
    # doesn't have an attribute called `app`.
    result = click_runner.invoke(run, ['logging:app'])
    assert result.exit_code != 0
    assert "Error: 'module' object has no attribute 'app'" in result.output


def test_run_non_henson_app(click_runner):
    """Tests that the run command fails with the incorrect app type."""
    result = click_runner.invoke(run, ['logging:INFO'])
    assert result.exit_code != 0
    assert ("Error: app must be an instance of a Henson application. Got "
            "<class 'int'>" in result.output)


def test_run_forever(click_runner, good_mock_service):
    """Tests that run_forever is called on the imported app."""
    result = click_runner.invoke(run, ['good_import:app'])
    assert result.exit_code == 0
    assert 'Run, Forrest, run!' in result.output
