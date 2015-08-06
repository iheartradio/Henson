"""Utilities for automatically reloading running applications."""

from importlib import reload
from threading import Thread

from watchdog.events import PatternMatchingEventHandler

__all__ = ('FunctionCallingEventHandler', 'ApplicationReloaderRunner')


class ApplicationReloaderRunner:

    """Wrap StoppableThread and restart when required."""

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

    """Restart a Henson application in response to filesystem events."""

    def __init__(self, target, args=(), kwargs={}, patterns=None,
                 ignore_patterns=None, ignore_directories=None,
                 case_sensitive=False):
        """Store the target function to be called on events."""
        super().__init__(
            patterns=patterns,
            ignore_patterns=ignore_patterns,
            ignore_directories=ignore_directories,
            case_sensitive=case_sensitive,
        )
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
