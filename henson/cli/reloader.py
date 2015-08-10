"""Utilities for automatically reloading running applications."""

from importlib import reload
from threading import Thread

from watchdog.events import PatternMatchingEventHandler

__all__ = ('FunctionCallingEventHandler', 'ApplicationReloaderRunner')


class ApplicationReloaderRunner:

    """Wrap StoppableThread and restart when required.

    Args:
        module (module): the module that should be reloaded after each
          change is detected
        app_name (str): the name of the :class:`~Henson.Application`
          instance that should be run
    """

    def __init__(self, module, app_name):
        """Store references to the module and app name to restart later."""
        self.module = module
        self.app_name = app_name
        self.thread = None

    def restart(self):
        """Stop any existing thread and start a new one in its place."""
        if self.thread is not None:
            self.thread.stop()
        self.module = reload(self.module)
        app = getattr(self.module, self.app_name)
        app.logger.info('Restarting {}.{}'.format(
            self.module.__name__,
            self.app_name,
        ))
        self.thread = StoppableThread(target=app.process_message)
        self.thread.start()


class FunctionCallingEventHandler(PatternMatchingEventHandler):

    """Restart a Henson application in response to filesystem events.

    Args:
        target (callable): the function to be run on every event emitted
          by the :class:`~watchdog.observers.Observer`.
        args (Optional[iterable]): positional arguments to be passed to
          the target function.
        kwargs (Optional[dict]): keyword arguments to be passed to the
          target function.
        patterns (Optional[iterable]): a list of string patterns.
          Filenames matching these patterns will cause events to fire,
          others will be ignored. Defaults to ``['*']``.
        ignore_patterns (Optional[iterable]): a list of string patterns.
          Filenames matching these patterns will be explicitly ignored
          for events. Mutually exclusive with ``patterns``, defaults to
          ``[]``.
        ignore_directories (Optional[bool]): whether or not to ignore
          directory-level changes. Defaults to ``False``.
        case_sensitive (Optional[bool]): whether or not patterns are
          case-sensitive. Defaults to ``False``.
    """

    def __init__(self, target, args=(), kwargs=None, patterns=None,
                 ignore_patterns=None, ignore_directories=False,
                 case_sensitive=False):
        """Store the target function to be called on events."""
        super().__init__(
            patterns=patterns,
            ignore_patterns=ignore_patterns,
            ignore_directories=ignore_directories,
            case_sensitive=case_sensitive,
        )

        if kwargs is None:
            kwargs = {}
        self.target = target
        self.args = args
        self.kwargs = kwargs

    def on_any_event(self, event):
        """Call the target function on any detected event."""
        self.target(*self.args, **self.kwargs)


class StoppableThread(Thread):

    """Thread subclass that allows for graceful stopping."""

    def stop(self):
        """Schedule the thread to stop at the next opportunity."""
        self.running = False

    def run(self):
        """Run the thread until it completes or is stopped."""
        self.running = True
        while self.running:
            self._target(*self._args, **self._kwargs)
