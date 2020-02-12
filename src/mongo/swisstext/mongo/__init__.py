"""
This package contains common definitions of the MongoDB collections used as part of the SwissText project.

Installation
------------

Simply run:

.. code-block:: bash

    python setup.py install

.. warning::

    The library ``cityhash`` is compiled during install and you need to have GCC and G++ installed,
    as well as the python header files. On Ubuntu, run:

    .. code-block:: bash

        apt install gcc g++ libdpkg-perl python3-dev

Collections
------------

The available collections are:

* `seeds`: the keywords used to search for new URLs using a search engine,
* `sentences`: the Swiss-German sentences found,
* `urls`: the URLs clawled so far that contained *at least one* Swiss German sentence,
* `blacklist`: all other URLs crawled,
* `users`: the users and their roles (for the frontend)

.. image:: https://docs.google.com/drawings/d/e/2PACX-1vQuDsGs0WcDIreW4WOjSrxSaONIqCAS9CzP8ajLVlxCqWaREGA1kJQWHvLsLnm8nkVI4w3wj1S6e86Y/pub?w=960&h=540

About the code
--------------

This package is required by
:py:mod:`swisstext.cmd`, which uses MongoEngine,
and :py:mod:`swisstext.frontend`, which uses `Flask-Mongoengine <http://docs.mongoengine.org/projects/flask-mongoengine>`_

The only way I found to make classes reusable by both is described in
`this issue <https://github.com/MongoEngine/flask-mongoengine/issues/309)>`_.

In short, the package :py:mod:`swisstext.mongo.abstract` defines "regular" MongoEngine documents, but also set
the meta flag `abstract` to `True`. Thus, those classes cannot be used as-is.

When using **MongoEngine**, just subclass each abstract class, as done in :py:mod:`swisstext.mongo.models`:

.. code-block:: python

    from swisstext.mongo.abstract import AbstractMongoURL
    class MongoURL(AbstractMongoURL):
        pass


When using **Flask-Mongoengine** do the same, but use a mixin so that documents also inherit from the
Flask Mongoengine Document class:

.. code-block:: python

    from flask_mongoengine import MongoEngine
    db = MongoEngine()

    from swisstext.mongo.abstract import AbstractMongoURL

    class MongoURL(db.Document, AbstractMongoURL):
        pass

"""