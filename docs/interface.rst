==================
Consumer Interface
==================

To work with Henson, a consumer must conform to the Consumer Interface. To
conform to the interface, the object must expose a :func:`~asyncio.coroutine`
function named ``read``.

Below is a sample implementation.

.. literalinclude:: file_consumer.py
