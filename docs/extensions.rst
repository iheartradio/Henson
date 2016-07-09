==========
Extensions
==========

Extensions provide additional functionality to applications. Configuration
management is shared between applications and extensions in a central location.

Using Extensions
================

.. code::

    from henson import Application
    from henson_sqlite import SQLite

    app = Application(__name__)
    db = SQLite(app)

    db.connection.execute('SELECT 1;')

Developing Extensions
=====================

Henson provides an :class:`~henson.extensions.Extension` base class to make
extension development easier.

.. code::

    from henson import Extension

    class SQLite(Extension):
        DEFAULT_SETTINGS = {'SQLITE_CONNECTION_STRING': ':memory:'}

        def __init__(self, app=None):
            self._connection = None
            super().__init__(app)

        @property
        def connection(self):
            if not self._connection:
                conn_string = self.app.settings['SQLITE_CONNECTION_STRING']
                self._connection = sqlite3.connect(conn_string)
            return self._connection

The :class:`~henson.extensions.Extension` class provides two special attributes
that are meant to be overridden:

* :attr:`~henson.extensions.Extension.DEFAULT_SETTINGS` provides default values
  for an extension's settings during the
  :meth:`~henson.extensions.Extension.init_app` step. When a value is used by
  an extension and has a sensible default, it should be stored here (e.g., a
  database hostname).
* :attr:`~henson.extensions.Extension.REQUIRED_SETTINGS` provides a list of
  keys that are checked for existence during the
  :meth:`~henson.extensions.Extension.init_app` step. If one or more required
  settings are not set on the application instance assigned to the extension, a
  ``KeyError`` is raised. Extensions should set this when a value is required
  but has no default (e.g., a database password).

.. _extending-the-cli:

Extending the Command Line
==========================

Henson offers an extensible command line interface. To register your own
commands, use :func:`~henson.cli.register_commands`. Any function passed to it
will have its usage created directly from its signature. In order to access the
new commands, the ``henson`` command line utility must be given a reference to
an :class:`~henson.base.Application`. This is done through the ``--app``
argument:

.. code::

    $ henson --app APP_PATH

.. note::

    For details about the syntax to use when passing a reference to an
    :class:`~henson.base.Application`, see :ref:`running-applications`.

A positional argument in the Python function will result in a required
positional argument in the command::

    def trash(grouch):
        pass

.. code:: sh

    $ henson --app APP_PATH NAMESPACE trash GROUCH

A keyword argument in the Python function will result in a positional argument
in the command with a default value to be used when the argument is omitted::

    def trash(grouch='oscar'):
        pass

.. code:: sh

    $ henson --app APP_PATH NAMESPACE trash [GROUCH]

A keyword-only argument in the Python function will result in an optional
argument in the command::

    def trash(*, grouch='oscar'):
        pass

.. code:: sh

    $ henson --app APP_PATH NAMESPACE trash [--grouch GROUCH]

By default, all optional arguments will have a flag that matches the function
argument's name. When no other optional arguments start with the same
character, a single-character abbreviated flag can also be used.

.. code:: sh

    $ henson --app APP_PATH NAMESPACE trash [-g GROUCH]

The ``trash`` function can then be registered with the CLI::

    register_commands('sesame', [trash])

.. code:: sh

    $ henson --app APP_PATH sesame trash --help

Available Extensions
====================

Several extensions are available for use:

* `Henson-AMQP <https://henson-amqp.rtfd.org>`_
* `Henson-Database <https://henson-database.rtfd.org>`_
* `Henson-Logging <https://henson-logging.rtfd.org>`_
