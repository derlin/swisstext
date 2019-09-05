"""
Classes for interacting with raw Text in the MongoDatabase.
"""

from datetime import datetime

from mongoengine import *

from cityhash import CityHash128


class AbstractMongoText(Document):
    """
    An abstract :py:class:`mongoengine.Document` for raw text of urls found in the ``urls`` collection.
    """

    id = StringField(primary_key=True)
    """The text hash, also used as a primary key."""

    urls = ListField(default=None)
    """Source URL(s) IDs."""

    text = StringField(default=None)
    """The actual text."""

    date_added = DateTimeField(default=lambda: datetime.utcnow())
    """When the first text was added to the collection, in UTC."""

    meta = {'collection': 'texts', 'abstract': True}

    @classmethod
    def exists(cls, text, hash=None) -> bool:
        """Test if a Text exists."""
        return cls.get(text, hash) is not None

    @classmethod
    def get(cls, text, hash=None) -> Document:
        """Get a Text instance."""
        if hash is None: hash = cls.get_hash(text)
        return cls.objects.with_id(hash)

    @classmethod
    def create(cls, url_id, text, hash=None) -> Document:
        """
        Create a Text. *Warning*: this **won't save** the document automatically.
        You need to call the ``.save`` method to persist it into the database.
        """
        if hash is None: hash = cls.get_hash(text)
        return cls(id=hash, urls=[url_id], text=text)

    @classmethod
    def create_or_update(cls, url_id, text, hash=None) -> Document:
        """
        Get or create a Text, adding the URL. *Warning*: this **won't save** the document automatically.
        You need to call the ``.save`` method to persist it into the database.

        Notes: if the hash of the text has already been computed for the text, it can be specified to avoid
        a recomputation; URL should be the id of the related URL document (a hash in latest versions).
        """
        if hash is None: hash = cls.get_hash(text)
        txt: Document = cls.get(text, hash=hash)
        if txt is not None:
            txt.update(add_to_set__urls=url_id)  # update
        else:
            txt = cls.create(url_id, text, hash=hash)  # create
        return txt

    @staticmethod
    def get_hash(text) -> str:
        """Hash the given text using
        `CityHash128 <https://opensource.googleblog.com/2011/04/introducing-cityhash.html>`_. """
        return str(CityHash128(text))
