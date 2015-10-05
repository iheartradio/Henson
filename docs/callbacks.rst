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

    def callback(application, message):
        yield 'spam'

    Application(..., callback=callback)

``message_preprocessors``
=========================

This is a list of callbacks that are intended to modify the incoming message
before it is passed to ``callback`` for processing.

.. code::

    def add_process_id(application, message):
        message['pid'] = os.getpid()
        return message

    Application(..., message_preprocessors=[add_process_id])

``result_postprocessors``
=========================

This is a list of callbacks are will operate on the result(s) of ``callback``.
Each callback is applied to each result.

.. code::

    def store_result(application, result):
        with open('/tmp/result', 'w') as f:
            f.write(result)

    Application(..., result_postprocessors=[store_result])

``error_callback``
==================

This callback is called when an error occurs while trying to read the next
message from the consumer.

.. code::

    def log_error(application, result):
        logger.error('spam')

    Application(..., error_callback=log_error)
