=========
Callbacks
=========

Henson operates on messages through a series of :func:`asyncio.coroutine`
callback functions. Each callback type serves a unique purpose.

``callback``
============

This is the only one of the callback settings that is required. Its purpose is
to process the incoming message. If desired, it should return the result(s) of
processing the message as an iterable.

.. code::

    async def callback(application, message):
        return ['spam']

    Application('name', callback=callback)

.. note:: There can only be one function registered as ``callback``.

``error``
==================

These callbacks are called when an exception is raised while processing a
message.

.. code::

    app = Application('name')

    @app.error
    async def log_error(application, message, exception):
        logger.error('spam')

.. note::

    Exceptions raised while postprocessing a result will not be processed
    through these callbacks.

``message_acknowledgement``
===========================

These callbacks are intended to acknowledge that a message has been received
and should not be made available to other consumers. They run after a message
and its result(s) have been fully processed.

.. code::

    app = Application('name')

    @app.message_acknowledgement
    async def acknowledge_message(application, original_message):
        await original_message.acknowledge()

``middleware``
=========================

These callbacks are called after each message is received and before it is
passed to ``callback``. Any modifications made to the message will be reflected
in what is passed to ``callback`` for processing.

.. code::

    app = Application('name')

    @app.middleware
    async def add_process_id(application, message):
        message['pid'] = os.getpid()
        return message

``postprocessor``
=========================

These callbacks will operate on the result(s) of ``callback``. Each callback is
applied to each result.

.. code::

    app = Application('name')

    @app.postprocessor
    async def store_result(application, result):
        with open('/tmp/result', 'w') as f:
            f.write(result)

``startup``
===========

These callbacks will run as an application is starting.

.. code::

    app = Application('name')

    @app.startup
    async def connect_to_database(application):
        await db.connect(application.settings['DB_HOST'])

``teardown``
============

These callbacks will run as an application is shutting down.

.. code::

    app = Application('name')

    @app.teardown
    async def disconnect_from_database(application):
        await db.close()
