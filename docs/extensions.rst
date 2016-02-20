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

Available Extensions
====================

Several extensions are available for use:

* `Henson-AMQP <https://github.com/iheartradio/Henson-AMQP>`_
* `Henson-Database <https://github.com/iheartradio/Henson-Database>`_
* `Henson-Logging <https://github.com/iheartradio/Henson-Logging>`_
