======
Henson
======

.. image:: _static/logo.png
   :width: 400
   :height: 400
   :align: center

Henson is a library for building services that are driven by consumers. Henson
applications read from objects that implement the :doc:`/interface` and provide
the message received to a callback for processing. The messsage can be
processed before handing it off to the callback, and the callback's results can
be processed after they are returned to the application.

.. note::

    This documentation uses the ``async``/``await`` syntax introduced to Python
    3.5 by way of `PEP 492 <https://www.python.org/dev/peps/pep-0492/>`_. If you
    are using an older version of Python, replace ``async`` with the
    ``@asyncio.coroutine`` decorator and ``await`` with ``yield from``.

Installation
============

You can install Henson using Pip::

    $ python -m pip install henson

.. warning::

    Henson hasn't been uploaded to the Python Package Index yet. Until that
    time, it must be installed from source.

You can also install it from source::

    $ python setup.py install

Quickstart
==========

.. code::

    # file_printer.py

    import asyncio

    from henson import Abort, Application

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

    async def callback(app, message):
        """Print the message retrieved from the file consumer."""
        print(app.name, 'received:', message)
        return message

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

    @app.middleware
    async def remove_comments(app, line):
        """Abort processing of comments (lines that start with #)."""
        if line.strip().startswith('#'):
            raise Abort('Line is a comment', line)
        return line


Running Applications
====================

Henson provides a ``henson`` command to run your applications from the command
line. To run the application defined in the quickstart above, ``cd`` to the
directory containing the module and run::

    $ henson run file_printer

If a module contains only one instance of a Henson
:class:`~henson.base.Application`, ``henson run`` will automatically detect and
run it. If more than one instance exists, the desired application's name must
be specified::

    $ henson run file_printer:app

This form always takes precedence over the former, and the ``henson`` command
won't attempt to auto-detect an instance even if there is a problem with the
name specified. If the attribute specified by the name after ``:`` is callable,
``henson run`` will call it and use the returned value as the application. Any
callable specified this way should require no arguments and return an instance
of :class:`~henson.base.Application`. Autodiscovery of callables that return
applications is not currently supported.

When developing locally, applications often need to be restarted as changes are
made. To make this easier, Henson provides a ``--reloader`` option to the
``run`` command. With this option enabled, Henson will watch an application's
root directory and restart the application automatically when changes are
detected::

    $ henson run file_printer --reloader

.. note:: The ``--reloader`` option is not recommended for production use.

It's also possible to enable Henson's `debug mode`_ through the ``--debug``
option::

    $ henson run file_printer --debug

Logging
=======

Henson applications provide a default logger. The logger returned by calling
:func:`logging.getLogger` will be used. The name of the logger is the name
given to the application. Any configuration needed (e.g.,
:func:`logging.basicConfig`, :func:`logging.config.dictConfig`, etc.) should be
done before the application is started.

.. _debug mode:

Debug Mode
==========

Debugging with asyncio can be tricky. Henson provides a debug mode enables
asyncio's debug mode as well as debugging information through Henson's logger.

Debug mode can be enabled through a configuration setting::

    app.settings['DEBUG'] = True

or by providing a truthy value for ``debug`` when calling
:meth:`~henson.base.Application.run_forever`::

    app.run_forever(debug=True)

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

