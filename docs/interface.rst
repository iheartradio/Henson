==================
Consumer Interface
==================

To work with Verona, a consumer must conform to the Consumer Interface. It must
be an object with a method called ``read`` that accepts no arguments. (The one
exception would be class or instance argument to a class or instance method.)
The ``read`` method must return an iterable.

Below is a sample implementation.

.. code::

    class FileConsumer:

        """Read files from a file."""

        def __init__(self, filename):
            self.filename = filename

        def read(self):
            """Return a generator that yields lines from the file."""
            with open(self.filename) as f:
                yield from f
