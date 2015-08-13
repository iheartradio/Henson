#!/usr/bin/env python

"""Collection of Henson CLI tasks."""

from importlib import find_loader, import_module
from threading import Thread

import os
import sys

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

import click

from .base import Application


@click.group(context_settings={'help_option_names': ('-h', '--help')})
def cli():
    """CLI entry point."""


@cli.command(context_settings={'help_option_names': ('-h', '--help')})
@click.option('--reloader/--no-reloader', default=False)
@click.argument('application_path')
def run(application_path, reloader):
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

    if reloader:
        # If the reloader is requested, create threads for running the
        # application and watching the file system for changes
        click.echo('Running {}.{} with reloader...'.format(
            import_path,
            app_name,
        ))

        # Find the root of the application and watch for changes
        watchdir = os.path.abspath(module.__file__)
        for _ in import_path.split('.'):
            watchdir = os.path.dirname(watchdir)

        # Create observer and runner threads
        observer = Observer()
        runner = Thread(target=app.run_forever)

        # This function is called by watchdog event handler when changes
        # are detected by the observers
        def restart_process(event):
            """Restart the process in-place."""
            os.execv(sys.executable, [sys.executable] + sys.argv[:])

        # Create the handler and watch the files
        handler = PatternMatchingEventHandler(
            patterns=['*.py', '*.ini'],
            ignore_directories=True,
        )
        handler.on_any_event = restart_process
        observer.schedule(handler, watchdir, recursive=True)

        # Start running everything
        runner.start()
        observer.start()

    else:
        # If the reloader is not needed, avoid the overhead
        click.echo('Running {}.{} forever...'.format(import_path, app_name))
        app.run_forever()

if __name__ == '__main__':
    sys.exit(cli())
