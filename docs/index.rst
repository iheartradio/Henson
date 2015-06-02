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

    if __name__ == '__main__':
        app.run_forever()

Contents:

.. toctree::
   :maxdepth: 1

   interface
   api


.. todo:: Testing


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
