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

Henson provides a base class to make extension development easier.

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

Available Extensions
====================

* `Henson-Database <https://github.com/iheartradio/Henson-Database>`_
* `Henson-Kafka <https://github.com/iheartradio/Henson-Kafka>`_
* `Henson-Logging <https://github.com/iheartradio/Henson-Logging>`_
