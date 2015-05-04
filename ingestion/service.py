"""Implementation of the service."""

from importlib import import_module
import sys

import click

from ingestion.kafka import connect, ConnectionInfo, Consumer



class Application:

    """This is a class."""

    _consumer = None

    def __init__(self, *, host, port, topic, callback, group=None):
        """Initialize the class."""
        self.info = ConnectionInfo(host, port, topic, group)
        self.callback = callback

    def _initialize(self):
        client = connect(host=self.info.host, port=self.info.port)

        self._consumer = Consumer(
            client=client, topic=self.info.topic, group=self.info.group)

    def run_forever(self):
        """Run the class."""
        if not self._consumer:
            self._initialize()

        messages = self._consumer.read()
        while True:
            try:
                message = next(messages)
            except KeyboardInterrupt:
                break
            except Exception:
                continue

            self.callback(message)


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.argument('service')
def run(service):
    """Run an ingestion service."""
    try:
        settings = import_module('{}.settings'.format(service))
    except ImportError:
        # If the service can't be imported or it doesn't contain the
        # necessary attributes, get out.
        raise click.BadOptionUsage(
            'service', '{} is not a valid service. No settings.'.format(service))
    try:
        process = import_module('{}.process'.format(service))
    except ImportError:
        # If the service can't be imported or it doesn't contain the
        # necessary attributes, get out.
        raise click.BadOptionUsage(
            'service', '{} is not a valid service. No process.'.format(service))
    app = Application(
        host=settings.KAFKA_BROKER_HOST,
        port=settings.KAFKA_BROKER_PORT,
        topic=settings.KAFKA_TOPIC_INBOUND,
        group=settings.KAFKA_GROUP_NAME,
        callback=process.run,
    )
    app.run_forever()


if __name__ == '__main__':
    sys.exit(run())
