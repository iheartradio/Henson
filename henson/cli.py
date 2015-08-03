#!/usr/bin/env python

"""Collection of Henson CLI tasks."""

from importlib import find_loader, import_module
import sys

import click

from .base import Application


@click.group(context_settings={'help_option_names': ('-h', '--help')})
def cli():
    """CLI entry point."""


@cli.command(context_settings={'help_option_names': ('-h', '--help')})
@click.argument('application_path')
def run(application_path):
    """Import and run an application."""
    # First, validate that the import path is specified in the correct
    # format
    try:
        import_path, app_name = application_path.split(':')
    except ValueError:
        raise click.BadOptionUsage('application_path',
                                   'application_path must be of the form '
                                   'path.to.module:application_name')

    # Add the present working directory to the import path so that
    # services can be found without installing them to site-packages
    # or modifying PYTHONPATH
    sys.path.insert(0, '.')

    # Then, try to find an import loader for the import_path
    # NOTE: this is to handle the case where a module is found but not
    # importable because of dependency import errors (Python 3 only)
    if not find_loader(import_path):
        raise click.BadOptionUsage('application_path',
                                   'Unable to find an import loader for '
                                   '{}.'.format(import_path))

    # Once found, import the module and handle any dependency errors
    try:
        module = import_module(import_path)
    except ImportError:
        raise click.BadOptionUsage('application_path',
                                   'Unable to import {}. Make sure all '
                                   'dependencies are installed and on '
                                   'PYTHONPATH.'.format(import_path))

    # Get the application from the module
    try:
        app = getattr(module, app_name)
    except AttributeError as e:
        raise click.BadOptionUsage('application_path', str(e))

    # Fail if the attribute specified is not a Henson application
    if not isinstance(app, Application):
        raise click.BadOptionUsage('application_path',
                                   'app must be an instance of a Henson '
                                   'application. Got {}'.format(type(app)))

    # Finally, run the app
    click.echo('Running {}.{} forever...'.format(import_path, app_name))
    app.run_forever()

if __name__ == '__main__':
    sys.exit(cli())
