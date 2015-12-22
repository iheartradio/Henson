"""Implementation of the service."""

import asyncio
import logging
import sys
import traceback

from .config import Config
from .exceptions import Abort

__all__ = ('Application',)


class Application:
    """A service application.

    Each message received from the consumer will be passed to the
    callback.

    Args:
        name (str): The name of the application.
        settings (Optional[object]): An object with attributed-based
            settings.
        consumer (optional): Any object that is an iterator or an
            iterable and yields instances of any type that is supported
            by ``callback``. While this isn't required, it must be
            provided before the application can be run.
        callback (Optional[asyncio.coroutine]): A callable object that
            takes two arguments, an instance of this class and the
            (possibly) preprocessed incoming message.  While this isn't
            required, it must be provided before the application can be
            run.
        error_callbacks (Optional[List[asyncio.coroutine]]): A list of
            callable objects that take three arguments: an instance of
            this class, the incoming message, and the exception that was
            raised. These callbacks will be called any time there is an
            exception while reading a message from the queue.
        message_preprocessors (Optional[List[asyncio.coroutine]]): A
            list of callable objects that take two arguments: an
            instance of this class and the incoming message. These
            callbacks will be called first for each incoming message and
            its return value will be passed to ``callback``.
        result_postprocessors (Optional[List[asyncio.coroutine]]): A
            list of callable objects that takes two arguments: an
            instance of this class and the each result of ``callback``.

    .. versionchanged:: 0.5.0

        ``callback``, ``error_callbacks``, ``message_preprocessors``,
        and ``result_postprocessors`` now require coroutines.

    .. versionchanged:: 0.4.0

        The ``message_preprocessors`` and ``result_postprocessors``
        parameters have been added to optionally preprocess an incoming
        msesage and postprocess all results.
    """

    def __init__(self, name, settings=None, *, consumer=None, callback=None,
                 error_callbacks=None, message_preprocessors=None,
                 result_postprocessors=None):
        """Initialize the class."""
        self.name = name

        # Configuration
        self.settings = Config()
        self.settings.from_object(settings or {})
        self.settings.setdefault('SLEEP_TIME', 0.1)

        # Callbacks
        self.callback = callback
        self.error_callbacks = error_callbacks or []
        self.message_preprocessors = message_preprocessors or []
        self.result_postprocessors = result_postprocessors or []

        self.consumer = consumer

        self.logger = logging.getLogger(self.name)

    def run_forever(self, num_workers=1, loop=None):
        """Consume from the consumer until interrupted.

        Args:
            num_workers (Optional[int]): The number of asynchronous
                tasks to use to process messages received through the
                consumer.  Defaults to 1.
            loop (Optional[asyncio.asyncio.BaseEventLoop]): An event
                loop that, if provided, will be used for running the
                application. If none is provided, the default event loop
                will be used.

        Raises:
            TypeError: If the consumer is None or the callback isn't
                callable.

        .. versionchanged:: 0.5.0

            Messages are now processed asynchronously. The
            ``num_workers`` parameter has been added to control how many
            futures are used to process them.
        """
        if self.consumer is None:
            raise TypeError('The consumer cannot be None.')

        _is_coroutine = asyncio.iscoroutinefunction

        if not _is_coroutine(self.callback):
            raise TypeError('The specified callback is not a coroutine.')

        if not all(_is_coroutine(cb) for cb in self.message_preprocessors):
            raise TypeError('Message preprocessors must be coroutines.')

        if not all(_is_coroutine(cb) for cb in self.result_postprocessors):
            raise TypeError('Result postprocessors must be coroutines.')

        if not all(_is_coroutine(cb) for cb in self.error_callbacks):
            raise TypeError('Error callbacks must be coroutines.')

        self.logger.info('application.started')

        # Use the specified event loop, otherwise use the default one.
        loop = loop or asyncio.get_event_loop()

        # Create an asynchronous queue to pass the messages from the
        # consumer to the processor. The queue should hold one message
        # for each processing task.
        queue = asyncio.Queue(maxsize=num_workers, loop=loop)

        # Create a task for the consumer.
        consumer = loop.create_task(self._consume(queue))

        # Create tasks to process each message received by the
        # consumer. The loop should wait until they are done.
        tasks = [
            loop.create_task(self._process(consumer, queue))
            for _ in range(num_workers)]

        try:
            # Run the loop forever.
            loop.run_forever()
        except BaseException as e:
            self.logger.error(e)

            # If something log wrong, cancel the consumer and restart
            # the loop. This will allow the futures to process all of
            # the messages in the queue and then exit cleanly.
            consumer.cancel()
            loop.run_until_complete(tasks)

            # Check for any exceptions that may have been raised by the
            # futures.
            self.logger.error(tasks.exception())
        finally:
            # Clean up after ourselves.
            loop.close()

        self.logger.info('application.stopped')

    @asyncio.coroutine
    def _abort(self, exc):
        """Log the aborted message.

        Args:
            exc (henson.exceptions.Abort): The exception to be logged.

        .. versionadded:: 0.5.0
        """
        tb = sys.exc_info()[-1]
        stack = traceback.extract_tb(tb, 1)[-1]
        self.logger.info(exc, message=exc.message, aborted_by=stack)

    @asyncio.coroutine
    def _apply_callbacks(self, callbacks, value):
        """Apply callbacks to a set of arguments.

        The callbacks will be called in the order in which they are
        specified, with the return value of each being passed to the
        next callback.

        Args:
            callbacks (List[callable]): The callbacks to apply to the
                provided arguments.
            value: The value to pass to the first callback.

        Returns:
            The return value of the final callback.

        .. versionadded:: 0.5.0
        """
        for callback in callbacks:
            value = yield from callback(self, value)
        return value

    @asyncio.coroutine
    def _consume(self, queue):
        """Read in incoming messages.

        Args:
            queue (asyncio.Queue): Any messages read in by the consumer
                will be added to the queue to share them with any future
                processing the messages.

        .. versionadded:: 0.5.0
        """
        while True:
            # Read messages and add them to the queue.
            value = yield from self.consumer.read()
            yield from queue.put(value)

    @asyncio.coroutine
    def _process(self, task, queue):
        """Process incoming messages.

        Args:
            task (asyncio.tasks.Task): The task populating ``queue``.
              The function will exit when it's been cancelled.
            queue (asyncio.Queue): A queue containing incoming messages
              to be processed.

        .. versionadded:: 0.5.0
        """
        while True:
            if queue.empty():
                # If there aren't any messages in the queue, check to
                # see if the consumer has been cancelled. If it has,
                # exit. Otherwise yield control back to the event loop
                # and then try again.
                if task.cancelled():
                    break

                yield from asyncio.sleep(self.settings['SLEEP_TIME'])
                continue

            message = yield from queue.get()

            try:
                message = yield from self._apply_callbacks(
                    self.message_preprocessors, message)
                self.logger.info('message.preprocessed')

                results = yield from self.callback(self, message)
            except Abort as e:
                yield from self._abort(e)
            except Exception as e:
                self.logger.error(
                    'message.failed', exc_info=sys.exc_info())
                for callback in self.error_callbacks:
                    # Any callback can prevent execution of further
                    # callbacks by raising StopIteration.
                    try:
                        yield from callback(self, message, e)
                    except StopIteration:
                        break
            else:
                yield from self._postprocess_results(results)

    @asyncio.coroutine
    def _postprocess_results(self, results):
        """Postprocess the results.

        Args:
            results (iterable): The results returned by processing the
                message.

        .. versionadded:: 0.5.0
        """
        if results is None:
            return

        # TODO: Evaluate this further. What are the pros and cons of
        # operating over multiple results versus keeping it just one.
        # As we look into asyncio, there may be benefits to yielding
        # from callback rather than returning.
        for result in results:
            try:
                yield from self._apply_callbacks(
                    self.result_postprocessors, result)
                self.logger.info('result.postprocessed')
            except Abort as e:
                yield from self._abort(e)
