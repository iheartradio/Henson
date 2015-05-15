######
Verona
######

A framework for running a Python service driven by a consumer.

.. code::

    from verona import Application

    class Consumer:
        def read(self):
            yield

    def callback(app, data):
        print(data)

    app = Application(__name__, consumer=consumer, callback=callback)

    if __name__ == '__main__':
        app.run_forever()
