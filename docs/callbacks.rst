=========
Callbacks
=========

Henson operates on messages through a series of callbacks. Each serves a unique
purpose.

``callback``
============

This is the only one of the callback settings that is required. Its purpose is
to process the incoming message. If desired, it should return the result(s) of
processing the message as an iterable.

.. code::

    async def callback(application, message):
        yield 'spam'

    Application('name', callback=callback)

``error``
==================

These callbacks are called when an error occurs while trying to read the next
message from the consumer.

.. code::

    app = Application('name')

    @app.error
    async def log_error(application, message, exception):
        logger.error('spam')

``message_acknowledgement``
===========================

These are callbacks that are intended to acknowledge that a message has been
received and should not be available to other consumers. They run after a
message and its result(s) have been fully processed.

.. code::

    app = Application('name')

    @app.message_acknowledgement
    async def acknowledge_message(application, original_message):
        await original_message.acknowledge()

``message_preprocessor``
=========================

These are callbacks that are intended to modify the incoming message before it
is passed to ``callback`` for processing.

.. code::

    app = Application('name')

    @app.message_preprocessor
    async def add_process_id(application, message):
        message['pid'] = os.getpid()
        return message

``result_postprocessor``
=========================

These are callbacks are will operate on the result(s) of ``callback``.  Each
callback is applied to each result.

.. code::

    app = Application('name')

    @app.result_postprocessor
    async def store_result(application, result):
        with open('/tmp/result', 'w') as f:
            f.write(result)

``startup``
===========

These are callbacks that will run when an application is starting.

.. code::

    app = Application('name')

    @app.startup
    async def connect_to_database(application):
        await db.connect(application.settings['DB_HOST'])

``teardown``
============

These are callbacks that will run when an application is shutting down.

.. code::

    app = Application('name')

    @app.teardown
    async def disconnect_from_database(application):
        await db.close()
