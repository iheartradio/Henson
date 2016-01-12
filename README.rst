######
Henson
######

.. image:: docs/_static/logo.png
   :width: 400
   :height: 400
   :align: center

A framework for running a Python service driven by a consumer.

.. code::

    from itertools import count

    from henson import Application

    def callback(app, data):
        print(data)

    app = Application(__name__, consumer=count(), callback=callback)

    if __name__ == '__main__':
        app.run_forever()
