======
Henson
======

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

You can also install it from source::

    $ python setup.py install

Quickstart
==========

.. literalinclude:: file_consumer.py

.. _running-applications:

Running Applications
====================

Henson provides a ``henson`` command to run your applications from the command
line. To run the application defined in the quickstart above, ``cd`` to the
directory containing the module and run::

    $ henson run file_printer

Henson's CLI can also be invoked by running the installed package as a script.
To avoid confusion and prevent different installations of Henson from
interfering with one another, this is the recommended way to run Henson
applications::

    $ python -m henson run file_printer

If a module contains only one instance of a Henson
:class:`~henson.base.Application`, ``python -m henson run`` will automatically
detect and run it. If more than one instance exists, the desired application's
name must be specified::

    $ python -m henson run file_printer:app

This form always takes precedence over the former, and the ``henson`` command
won't attempt to auto-detect an instance even if there is a problem with the
name specified. If the attribute specified by the name after ``:`` is callable,
``python -m henson run`` will call it and use the returned value as the
application. Any callable specified this way should require no arguments and
return an instance of :class:`~henson.base.Application`. Autodiscovery of
callables that return applications is not currently supported.

When developing locally, applications often need to be restarted as changes are
made. To make this easier, Henson provides a ``--reloader`` option to the
``run`` command. With this option enabled, Henson will watch an application's
root directory and restart the application automatically when changes are
detected::

    $ python -m henson run file_printer --reloader

.. note:: The ``--reloader`` option is not recommended for production use.

It's also possible to enable Henson's `debug mode`_ through the ``--debug``
option::

    $ python -m henson run file_printer --debug

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


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

