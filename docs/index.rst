======
Henson
======

Henson is a library for building services that are driven by consumers. Henson
applications read for objects that implement the :doc:`/interface` and provide
data received to a callback for processing.

Installation
============

If you are using the internal package index server, you can install Henson
using Pip::

    $ pip install henson

Otherwise, Henson can be installed from source::

    $ python setup.py install

Quickstart
==========

.. code::

    # file_printer.py

    import asyncio

    from henson import Application, Abort

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

    async def callback(app, data):
        """Print the data retrieved from the file consumer."""
        print(app.name, 'received:', data)
        return data

    app = Application(
        __name__,
        callback=callback,
        consumer=FileConsumer(__file__),
    )

    @app.startup
    async def print_header(app):
        """Print a header for the file being processed."""
        print('# Begin processing', app.consumer.filename)

    @app.teardown
    async def print_footer(app):
        """Print a footer for the file being processed."""
        print('# Done processing', app.consumer.filename)

    @app.message_preprocessor
    async def remove_comments(app, line):
        """Abort processing of comments (lines that start with #)."""
        if line.strip().startswith('#'):
            raise Abort('Line is a comment', line)
        return line


Running Applications
====================

Henson provides a CLI command to run your applications. To run the application
defined in the quickstart above, cd to the directory containing the module and
run::

    $ henson run file_printer

If a module contains only one instance of a Henson
:class:`~henson.base.Application`, ``henson run`` will automatically detect
this and run it. If more than one application exists within the module, the
desired application's name must be specified, e.g.  ``henson run
file_printer:app``. This form always takes precedence over the former, and the
henson cli will not attempt to fall back to an auto-detected application if
there is a problem with the name specified. If the attribute specified by the
name after ``:`` is callable, ``henson run`` will call it and use the returned
value as the application. Any callable specified this way should require no
arguments and return an instance of an :class:`~henson.base.Application`.
Autodiscovery of callables that return applications is not currently supported.

When developing locally, applications often need to be restarted as changes are
made. To make this easier, Henson provides a ``--reloader`` option to the
``run`` command. With this option enabled, Henson will watch an application's
root directory and restart the application automatically when changes are
detected::

    $ henson run file_printer:app --reloader

.. note:: The ``--reloader`` option is not recommended for production use.

Logging
=======

Henson applications provide a default logger. The logger returned by calling
:func:`logging.getLogger` will be used. The name of the application will be
used to specify which logger to use. Any configuration needed should (e.g.,
:func:`logging.basicConfig`, :func:`logging.config.dictConfig`) should be done
before the application is started.

Contents:

.. toctree::
   :maxdepth: 1

   interface
   callbacks
   extensions
   contrib
   api
   changes


.. todo:: Testing


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

