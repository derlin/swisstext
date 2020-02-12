"""
Implementation of the classes defined in :py:mod:`swisstext.mongo.abstract` for use with :py:mod:`mongoengine`
(and not :py:mod:`flask-mongoengine`).

Example usage:

.. code-block:: python

    from mongoengine import connect
    from swisstext.mongo.models import *

    connect(db='swisstext') # default host and port: localhost:27017

    # Get all urls in the urls collection
    all_urls = MongoURL.objects
    all_urls.count() # print the size of the cursor

    # Get one url by ID
    url = 'http://example.com'
    MongoURL.objects.with_id(url) # returns either a MongoURL or None

    # A more complex query:
    # get all URLs containing 'wikipedia' that have been crawled at least once and
    # with less than 10 new URLs found and sort the results by last crawl date, descending
    MongoURL \
        .objects(
            id__icontains="wikipedia",
            crawl_history__0__exists=True,
            count__lt=10
        ) \
        .order_by('-delta_date')

.. seealso::

   Module :py:mod:`swisstext.mongo.abstract`
      Documentation of all the classes. Simply look for ``Abstract<Classname>``.

   `MongoEngine documentation <http://docs.mongoengine.org/>`_
      The MongoEngine documentation, including the API reference.

"""

from .abstract import *


def get_connection(db='st1', host='localhost', port=27017, **kwargs):
    from mongoengine import connect
    return connect(db, host=host, port=port)


class MongoUser(AbstractMongoUser):
    pass


class MongoBlacklist(AbstractMongoBlacklist):
    pass


class MongoURL(AbstractMongoURL):
    pass


class MongoSeed(AbstractMongoSeed):
    pass


class MongoSentence(AbstractMongoSentence):
    pass

class MongoText(AbstractMongoText):
    pass