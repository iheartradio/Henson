"""Implementation of the service."""

import sys

import click

from ingestion.kafka import Kafka
from ingestion.importer import import_from_service, ServiceImportError
from ingestion.registry import Registry

__all__ = ('Application',)

registry = Registry()


class Application:

    """A service application.

    A service application will spin up its own Kafka consumer and pass
    each incoming message to a callback.

    Args:
        name (str): The name of the application.
        settings (object): An object with attributed-based settings.
        callback (callable): A callable object that takes two
          arguments, an instance of this class and a dict representing
          an incoming message.
    """

    def __init__(self, name, settings, *, callback):
        """Initialize the class."""
        self.name = name
        self.settings = dict()
        self.settings.update(object_to_settings(settings))
        self.callback = callback

        self.kafka = Kafka(self)

        registry.current_application = self

    def run_forever(self):
        """Run the class."""
        consumer = self.kafka.consumer()

        messages = consumer.read()
        while True:
            try:
                message = next(messages)
            except KeyboardInterrupt:
                break
            except Exception:
                continue

            self.callback(self, message)


def object_to_settings(obj):
    """Convert an object into a structure usable for settings.

    Uppercase attributes of the specified object will be included in a
    new mapping that can be used to update existing settings.

    Args:
        obj: An object encapsulating settings. This will typically be a
          module or class.

    Returns:
        dict: A mapping of the settings taken from the object.

    .. versionadded:: 0.3.0
    """
    return {key: getattr(obj, key) for key in dir(obj) if key.isupper()}


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.argument('service')
def run(service):
    """Run an ingestion service."""
    try:
        settings = import_from_service(service, 'settings')
    except ServiceImportError as e:
        raise click.BadOptionUsage('service', str(e))
    try:
        process = import_from_service(service, 'process')
    except ServiceImportError as e:
        raise click.BadOptionUsage('service', str(e))
    app = Application(
        name=service,
        settings=settings,
        callback=process.run,
    )
    app.run_forever()


if __name__ == '__main__':
    sys.exit(run())
