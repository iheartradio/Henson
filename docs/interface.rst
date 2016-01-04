==================
Consumer Interface
==================

To work with Henson, a consumer must conform to the Consumer Interface. To
conform to the interface, the object must expose a coroutine named ``read``.

Below is a sample implementation.

.. code::

    import asyncio

    class FileConsumer:
        """Read lines from a file."""

        def __init__(self, filename):
            self.filename = filename
            self._file = None

        def __iter__(self):
            """FileConsumer objects are iterators."""
            return self

        def __next__(self):
            """Return the next line of the file, if available."""
            if not self._file:
                self._file = open(self.filename)
            try:
                return next(self._file)
            except StopIteration:
                self._file.close()
                raise Abort('Reached end of file', None)

        async def read(self):
            """Return the next line in the file."""
            return next(self)
