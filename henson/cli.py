#!/usr/bin/env python

"""Collection of Henson CLI tasks."""

from importlib import import_module
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
    try:
        import_path, app_name = application_path.split(':')
    except ValueError:
        raise click.BadOptionUsage('application_path',
                                   'application_path must be of the form '
                                   'path.to.module:application_name')
    try:
        module = import_module(import_path)
    except ImportError:
        raise click.BadOptionUsage('application_path',
                                   'Unable to import {}. Is it on the '
                                   'PYTHONPATH?'.format(import_path))
    try:
        app = getattr(module, app_name)
    except AttributeError as e:
        raise click.BadOptionUsage('application_path', str(e))
    if not isinstance(app, Application):
        raise click.BadOptionUsage('application_path',
                                   'app must be an instance of a Henson '
                                   'application. Got {}'.format(type(app)))
    click.echo('Running {}.{} forever...'.format(import_path, app_name))
    app.run_forever()

if __name__ == '__main__':
    sys.exit(cli())
