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

    # file: file_printer.py

    from henson import Application

    class FileConsumer:
        def __init__(self, filename):
            self.filename = filename

        def __iter__(self):
            with open(self.filename) as f:
                yield from f

    def callback(app, data):
        print(app.name, 'received:', data)

    app = Application(__name__)
    app.callback = callback
    app.consumer = FileConsumer(__file__)

Running Applications
====================

Henson provides a CLI command to run your applications. To run the application
defined in the quickstart above, ``cd`` to the directory containing the module
and run::

    $ henson run file_printer:app

When developing locally, applications often need to be restarted as changes are
made. To make this easier, Henson provides a ``--reloader`` option to the
``run`` command. With this option enabled, Henson will watch an application's
root directory and restart the application automatically when changes are
detected::

    $ henson run file_printer:app --reloader

.. note:: The ``--reloader`` option is not recommended for production use.

Logging
=======

Henson applications provide a default logger. By default, the logger returned
by calling :func:`logging.getLogger` will be used. The name of the application
will be used to specify which logger to use. Any configuration needed should be
done (e.g., :func:`logging.basicConfig`, :func:`logging.config.dictConfig`)
should be done before the application is started.

If you want to use a specific logger instance with your application, however,
you can provide it when you instantiate the application::

    app = Application(__name__, logger=logging.getLogger('specificlogger'))

While this example is a bit contrived, this is useful if you want to use
third-party loggers (e.g., `structlog <http://structlog.rtfd.org>`_) to handle
your logging::

    import structlog

    app = Application(__name__, logger=structlog.get_logger())

Contents:

.. toctree::
   :maxdepth: 1

   interface
   extensions
   api
   changes


.. todo:: Testing


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

