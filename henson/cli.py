"""Collection of Henson CLI tasks."""

import asyncio
from importlib import find_loader, import_module
import os
import sys
from threading import Thread

from argh import ArghParser, CommandError
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

from . import __version__
from .base import Application


def run(application_path, reloader=False, workers=1, debug=False):
    """Import and run an application.

    Args:
        application_path (str): The path to the application that should
            be imported and run.
        reloader (Optional[bool]): Whether or not to watch for changes
            within an application and reload the running instance when
            they are detected. Not recommended for production use.
            Defaults to False.
        workers (Optional[int]): How many async workers the application
            should use to process messages. Defaults to 1.
        debug (Optional[bool]): Whether or not to run the application
            with debug mode enabled. Defaults to False.
    """
    # Add the present working directory to the import path so that
    # services can be found without installing them to site-packages
    # or modifying PYTHONPATH
    sys.path.insert(0, '.')

    # First, find the module that should be imported
    application_path_parts = application_path.split(':', 1)
    import_path = application_path_parts.pop(0)

    # Then, try to find an import loader for the import_path
    # NOTE: this is to handle the case where a module is found but not
    # importable because of dependency import errors (Python 3 only)
    if not find_loader(import_path):
        raise CommandError(
            'Unable to find an import loader for {}.'.format(import_path),
        )

    # Once found, import the module and handle any dependency errors
    # TODO: Wrap the ImportError raised here to provide more meaningful
    # error messages to the end user
    module = import_module(import_path)

    # If an application name is specified, use that to select the
    # application instance
    try:
        app_name = application_path_parts.pop()
        # TODO: Wrap the AttributeError raised here to provide more
        # meaningful error messages to the end user
        app = getattr(module, app_name)
        # If the attribute specified by app_name is a callable, assume
        # it is an application factory and call it to get an instance of
        # a Henson application.
        if callable(app):
            app = app()
        # Fail if the attribute specified is not a Henson application
        if not isinstance(app, Application):
            raise CommandError(
                'app must be an instance of a Henson application. '
                'Got {}'.format(type(app)),
            )

    # If no application name is specified, try to automatically select
    # the correct module attribute based on type
    except IndexError:
        app_candidates = []
        for name in dir(module):
            attr = getattr(module, name)
            if isinstance(attr, Application):
                app_candidates.append((name, attr))

        # If there are zero app_candidates, there's nothing to run.
        if not app_candidates:
            raise CommandError(
                'No Henson application found. Please specify the '
                'application by name or run a different module.',
            )

        # If there are more than one, the choice of which app to run is
        # ambiguous.
        if len(app_candidates) > 1:
            raise CommandError(
                'More than one Henson application found in {}. Please '
                'specify a application by name (probably one of [{}]).'.format(
                    import_path, ', '.join(ac[0] for ac in app_candidates)),
            )

        app_name, app = app_candidates[0]

    if reloader or debug:
        # If the reloader is requested (or debug is enabled), create
        # threads for running the application and watching the file
        # system for changes.
        print('Running {}.{} with reloader...'.format(
            import_path,
            app_name,
        ))

        # Find the root of the application and watch for changes
        watchdir = os.path.abspath(module.__file__)
        for _ in import_path.split('.'):
            watchdir = os.path.dirname(watchdir)

        # Create observer and runner threads
        observer = Observer()
        loop = asyncio.new_event_loop()
        runner = Thread(
            target=app.run_forever,
            kwargs={'num_workers': workers, 'loop': loop, 'debug': debug},
        )

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
        print('Running {}.{} forever ...'.format(import_path, app_name))
        app.run_forever(num_workers=workers, debug=debug)


def main():
    """Dispatch the CLI command to the target function."""
    return parser.dispatch()


# Define a parser and add commands to it.
parser = ArghParser()
parser.add_argument('--version', action='version', version=__version__)
parser.add_commands([run])
