"""
This module contains abstract :py:class:`mongoengine.Document` definitions for all the objects in the SwissText system
database.

When using mongoengine directly, you can use the concrete classes defined in :py:mod:`swisstext.mongo.models`.

When using Flask-MongoEngine, just subclass all abstract classes (i.e. the ones prefixed with `Abstract`)
and make them inherit from ``db.Document`` as well. For example:

.. code-block:: python

    from flask_mongoengine import MongoEngine
    db = MongoEngine()

    from swisstext.mongo.abstract import AbstractMongoURL

    class MongoURL(db.Document, AbstractMongoURL):
        pass
"""
from .generic import SourceType, Source, Deleted, Dialects
from .urls import AbstractMongoURL, AbstractMongoBlacklist
from .seeds import AbstractMongoSeed
from .users import AbstractMongoUser, UserRoles
from .sentences import AbstractMongoSentence, DialectInfo, DialectEntry
from .text import AbstractMongoText