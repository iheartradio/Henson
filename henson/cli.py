"""Collection of Henson CLI tasks."""

from argparse import Action
from collections import Counter
from copy import deepcopy
from contextlib import suppress
from functools import wraps
from importlib import find_loader, import_module
import inspect
import logging
import os
import sys
from threading import Thread

from argh import ArghParser, CommandError
from argh.decorators import arg, expects_obj
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

from . import __version__
from .base import Application, _new_event_loop

__all__ = ('register_commands',)


def register_commands(namespace, functions, namespace_kwargs=None,
                      func_kwargs=None):
    """Register commands with the henson CLI.

    The signature of each function provided through ``functions`` will
    be mapped to its command's interface. Any positional arguments in
    the function's signature will become required positional arguments
    to the command. Keyword arguments in the signature will also become
    positional arguments, although they will use the default value from
    the signature when not specified on the command line. Keyword-only
    arguments in the signature will become optional arguments on the
    command line.

    Args:
        namespace (str): A name representing the group of commands. The
            namespace is required to access the commands being added.
        functions (List[callable]): A list of callables that are used to
            create subcommands. More details can be found in the
            documentation for :func:`~argh.assembling.add_commands`.

    .. note::

        This function is a wrapper around
        :func:`~argh.assembling.add_commands`. Please refer to its
        documentation for any arguments not explained here.

    .. versionadded:: 1.1.0
    """
    commands = []

    if func_kwargs is None:
        func_kwargs = {}

    for function in functions:
        # Inspect the function first. While everything it returns can be
        # captured from the function object itself, the function will be
        # decorated by the code below, altering its signature.  Using
        # inspect here will capture a snapshot that can be used without
        # alteration.
        spec = inspect.getfullargspec(function)

        # app is registered as an argument to the henson entry point
        # directly. If the function accepts it as an argument, we need
        # to make argh think the function accepts a namespace as its
        # only argument, with all arguments being specified through the
        # arg decorator. Using a namespace is also what allows us to
        # treat keyword arguments as optional positional arguments, so
        # all functions are wrapped by expects_obj and then
        # _with_namespace.
        accepts_app = 'app' in spec.args
        function = _with_namespace(expects_obj(function), accepts_app)

        with suppress(ValueError):
            # Remove app from the list of arguments so that it doesn't
            # get registered twice.
            spec.args.remove('app')

        # Associate values with keyword arguments.
        if not spec.defaults:
            # None isn't iterable.
            defaults = {}
        else:
            defaults = dict(zip(
                spec.args[-len(spec.defaults):],
                spec.defaults))

        # Keyword-only arguments are exposed to the command line as
        # optional arguments. By default two flags are available for
        # each: an abbreviated name (the first character) and a full
        # name (with dashes instead of underscores). If two arguments
        # share the same first letter, however, the abbreviated flags
        # won't be used for them.
        conflicts = Counter(a[0] for a in spec.kwonlyargs)
        conflicts = tuple(k for k, v in conflicts.items() if v > 1)

        # Iterate over the rest of the arguments. Positional and keyword
        # arguments are combined by inspect, but keyword-only arguments
        # are separate. They all need to be combined so that they can be
        # iterated over in reverse order. The reverse is needed to
        # retain the order of positional arguments as specified by the
        # function's signature.
        arguments = spec.args + spec.kwonlyargs

        # Set up the keyword argument overrides.
        func_kwargs = deepcopy(func_kwargs)

        # First, check for verbosity-related arguments since those are
        # handled in a special way. Remove any that are found from the
        # list of all arguments so they aren't processed again later.
        if any(arg in arguments for arg in ('quiet', 'verbose')):
            if 'quiet' not in arguments:
                # Add just the verbose argument.
                decorator = arg(
                    '--verbose', '-v', action='count', help='verbose mode')
                function = decorator(function)
            elif 'verbose' not in arguments:
                # Add just the quiet argument.
                decorator = arg(
                    '--quiet', '-q', action='count', help='quiet mode')
                function = decorator(function)
            else:
                # Add the mutually exclusive group (through parent).
                func_kwargs['parents'] = [parent]

            with suppress(ValueError):
                arguments.remove('verbose')
            with suppress(ValueError):
                arguments.remove('quiet')

        for argument in reversed(arguments):
            kwargs = {}
            if argument in spec.kwonlyargs:
                # Treat keyword-only arguments as optional arguments.
                kwargs['default'] = spec.kwonlydefaults[argument]
                flags = (
                    '-{0}'.format(argument[0]),
                    '--{0}'.format(argument).replace('_', '-'),
                )
                if argument.startswith(conflicts):
                    flags = flags[1:]
            else:
                # Treat all other arguments as positional arguments.
                # Keyword arguments will be handled as positional
                # arguments with default values.
                with suppress(KeyError):
                    # The argument will only be included in defaults
                    # for keyword arguments.
                    kwargs['default'] = defaults[argument]
                    kwargs['nargs'] = '?'

                # The argument's name is replaced by a list of flags for
                # keyword-only arguments. Simulate that here so that the
                # same call to arg can be used for all arguments.
                flags = [argument]

            with suppress(KeyError):
                kwargs['help'] = spec.annotations[argument]

            function = arg(*flags, **kwargs)(function)

        # Add the function to the list of commands to add to the parser.
        commands.append(function)

    parser.add_commands(
        namespace=namespace,
        functions=commands,
        namespace_kwargs=namespace_kwargs,
        func_kwargs=func_kwargs,
    )


@arg('-v', '--verbose', action='count', help='verbose mode')
def run(
        application_path: 'the path to the application to run',
        reloader: 'reload the application on changes' = False,
        workers: 'the number of asynchronous tasks to run' = 1,
        debug: 'enable debug mode' = False,
        **kwargs):
    """Import and run an application."""
    if kwargs['quiet']:
        # If quiet mode has been enabled, set the number of verbose
        # flags to -1 so that the level above warning will be used.
        verbosity = -1
    else:
        # argparse gives None not 0.
        verbosity = kwargs['verbose'] or 0

    # Set the log level based on the number of verbose flags. Do this
    # before the app is imported so any log calls made will respect the
    # specified level.
    log_level = logging.WARNING - (verbosity * 10)
    logging.basicConfig(level=log_level)

    import_path, app = _import_application(application_path)

    # Now that we have an application, set it's log level, too.
    app.logger.setLevel(log_level)

    if reloader or debug:
        # If the reloader is requested (or debug is enabled), create
        # threads for running the application and watching the file
        # system for changes.
        app.logger.info('Running {!r} with reloader...'.format(app))

        # Find the root of the application and watch for changes
        watchdir = os.path.abspath(import_module(import_path).__file__)
        for _ in import_path.split('.'):
            watchdir = os.path.dirname(watchdir)

        # Create observer and runner threads
        observer = Observer()
        loop = _new_event_loop()
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
        app.logger.info('Running {!r} forever...'.format(app))
        app.run_forever(num_workers=workers, debug=debug)


class _ApplicationAction(Action):
    """A custom action to import an application."""

    def __call__(self, parser, namespace, values, option_string=None):
        _, application = _import_application(values)
        setattr(namespace, self.dest, application)


def main():
    """Dispatch the CLI command to the target function."""
    return parser.dispatch()


def _import_application(application_path):
    """Return the imported application and the path to it.

    Args:
        application_path (str): The path to use to import the
            application. It should be in the form of ``PATH[:APP]``.

    Returns:
        Tuple[str, henson.base.Application]: A two-tuple containing the
            import path and the imported application.
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

    return import_path, app


def _with_namespace(f, include_app):
    """Call the function with the parsed arguments."""
    @wraps(f)
    def inner(parsed_args):
        parsed_args = vars(parsed_args)
        parsed_args.pop('_functions_stack', None)
        if not include_app:
            parsed_args.pop('app')
        return f(**parsed_args)
    return inner


# Create a parent group so that arguments such as --verbose can be added
# to all commands.
parent = ArghParser(add_help=False)

# Create a mutually exclusive group to control the verbosity. verbose
# and quiet will be provided under kwargs.
chatter = parent.add_mutually_exclusive_group()
chatter.add_argument('--verbose', '-v', action='count', help='verbose mode')
chatter.add_argument('--quiet', '-q', action='count', help='quiet mode')

# Define a parser and add commands to it.
parser = ArghParser()
parser.add_argument('--version', action='version', version=__version__)

# Add an argument to import an application to load its CLI extensions.
parser.add_argument(
    '-a', '--app',
    action=_ApplicationAction,
    help='the path to the application to run',
)

parser.add_commands([run], func_kwargs={'parents': [parent]})
