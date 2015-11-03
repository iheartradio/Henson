==================
Consumer Interface
==================

To work with Henson, a consumer must conform to the Consumer Interface. To
conform to the interface, the object must expose a coroutine named ``read``.

Below is a sample implementation.

.. code::

    import asyncio

    class FileConsumer:
        """Read files from a file."""

        def __init__(self, filename):
            self.filename = filename

        def __iter__(self):
            """Return a generator that yields lines from the file."""
            with open(self.filename) as f:
                yield from f

        @asyncio.coroutine
        def read(self):
            """Return the next line in the file."""
            return next(self)
