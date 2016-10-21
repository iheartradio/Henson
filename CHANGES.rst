Version 1.1.1
-------------

Release TBD

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
