==================
Consumer Interface
==================

To work with Henson, a consumer must conform to the Consumer Interface. To
conform to the interface, the object must be iterable. It can be a built-in
type, a generator, a custom class with an ``__iter__`` method, etc.

Below is a sample implementation.

.. code::

    class FileConsumer:

        """Read files from a file."""

        def __init__(self, filename):
            self.filename = filename

        def __iter__(self):
            """Return a generator that yields lines from the file."""
            with open(self.filename) as f:
                yield from f

This can be simplified to just use the stream object directly.

.. code::

    with open(filename) as f:
        # f can be used as the consumer.
