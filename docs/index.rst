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

    from henson import Application

    class FileConsumer:
        def __init__(self, filename):
            self.filename = filename

        def __iter__(self):
            with open(self.filename) as f:
                yield from f

        @asyncio.coroutine
        def read(self):
            return next(self)

    @asyncio.coroutine
    def callback(app, data):
        print(app.name, 'received:', data)
        return data

    app = Application(__name__)
    app.callback = callback
    app.consumer = FileConsumer(__file__)

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
there is a problem with the name specified.

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

