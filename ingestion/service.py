"""Implementation of the service."""

import sys

import click

from ingestion.kafka import connect, ConnectionInfo, Consumer
from ingestion.importer import import_from_service, ServiceImportError


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
        self.settings = settings
        self.callback = callback

        # KafkaClient connections are eager. Don't instantiate an
        # instance until we're ready to use it.
        self._consumer = None
        self._consumer_info = ConnectionInfo(
            settings.KAFKA_BROKER_HOST,
            settings.KAFKA_BROKER_PORT,
            settings.KAFKA_TOPIC_INBOUND,
            settings.KAFKA_GROUP_NAME,
        )

    def _initialize(self):
        client = connect(
            host=self._consumer_info.host, port=self._consumer_info.port)

        self._consumer = Consumer(
            client=client,
            topic=self._consumer_info.topic,
            group=self._consumer_info.group,
        )

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

            self.callback(self, message)


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
