Version 2.3.0
-------------

Released TBD

- add support for settings overrides in the ``contrib`` package, ``retry``.

Version 2.2.0
-------------

Released 2021-01-29

- Drop support for Python < 3.8, add support for Python >= 3.8

Version 2.1.0
-------------

Released 2020-04-13

- Adding a boolean setting `ASYNC_QUEUE` to support
  using either Synchronous Queue (when False) 
  or Async Queue(when true) [default]

Version 2.0.0
-------------

Released 2019-08-01

- Add support for Python 3.7
- Deprecate support for Python 3.4

Version 1.2.0
-------------

Released 2018-04-04

- Unhandled exceptions raised while processing a message will stop the
  application
- Set the event loop when running with the reloader

Version 1.1.0
-------------

Released 2016-11-11

- Add ``henson.cli.register_commands`` to extend the command line interface
- Messages are logged using ``logging.DEBUG`` instead of ``logging.INFO``
- Calls to ``print`` in ``henson.cli.run`` are updated to ``app.logger.info``
- References to objects used by ``henson.Application`` are removed once they
  are no longer needed to allow the memory to be freed up before the next
  message is received.
- uvloop_ will be used for the event loop if it's installed.
- Automatically register extensions to a registry on the application
- Add ``hensoncli`` Sphinx directive to document extensions to the command line
  interface
- ``henson.cli.run`` and any command line extensions that request it support
  ``quiet`` and ``verbose`` flags to set verbosity

Version 1.0.0
-------------

Released 2016-03-01

- Initial release

.. _uvloop: https://uvloop.readthedocs.io
