"""
Classes for interacting with Users in the MongoDatabase.

A user has a username and a password, as well as a list of possible roles to fine-grain the access to the frontend.
"""

import hashlib
from mongoengine import *


class UserRoles:
    """Currently, users can either be :py:attr:`ADMIN` or :py:attr:`USER`."""
    ADMIN = "admin"
    USER = "user"


class AbstractMongoUser(Document):
    # the ID field type
    # TODO: use a uuid instead ?
    _id_type = StringField

    id = _id_type(primary_key=True)
    """The user ID, which is also the username."""

    password = StringField()
    """
    The password, hashed using MD5.
    
    In python:
    
    .. code-block:: python
    
        import hashlib
        hashlib.md5(password.encode()).hexdigest()
    
    In Mongo Shell:
    
    .. code-block:: javascript
    
        hex_md5(password)
        
    """

    roles = ListField(StringField(), default=[])
    """The list of roles. If the list is empty, the user is considered a :py:attr:`~UserRoles.USER`. """
    meta = {'collection': 'users', 'abstract': True}

    @staticmethod
    def get_hash(password) -> str:
        """Generate the MD5 hash of the password."""
        return hashlib.md5(password.encode()).hexdigest()

    @classmethod
    def get(cls, uuid: str, password: str = None):
        """
        Get a user. If password is specified, it is checked against the one in the database (login).

        :param uuid: the username / ID
        :param password: the clear password
        :return: either a user instance or None if the uuid does not exist or the password was specified and incorrect.
        """
        u = cls.objects.with_id(uuid)
        if u and password is not None:
            return u if cls.get_hash(password) == u.password else None
        return u
