======================
Command Line Interface
======================

Henson provides the following command line interface.

.. autoprogram:: henson.cli:parser
   :prog: henson

Further Details
===============

When developing locally, applications often need to be restarted as changes are
made. To make this easier, Henson provides a ``--reloader`` option to the
``run`` command. With this option enabled, Henson will watch an application's
root directory and restart the application automatically when changes are
detected::

    $ python -m henson run file_printer --reloader

.. note:: The ``--reloader`` option is not recommended for production use.

It's also possible to enable Henson's :ref:`debug mode` through the ``--debug``
option::

    $ python -m henson run file_printer --debug

.. note:: The ``--debug`` option is not recommended for production use.

This will also enable the reloader.

Extending the Command Line
==========================

For information about how to extension Henson's command line interface, see
:ref:`extending-the-cli`.
