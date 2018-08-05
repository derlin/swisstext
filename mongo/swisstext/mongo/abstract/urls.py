"""
Classes for interacting with URLs in the MongoDatabase.

All visited URLs must be recorded in some way in the database, at least to avoid recawling over and over the same
links. Thus, URLs are splitted into two collections:

* `urls`: stores *interesting* URLs that could/should be crawled again,
* `blacklist`: stores URLs that should never by visited again.

At the time of writing, :py:mod:`swisstext.cmd.scraping` defines interesting URLs as URLs with at least one
Swiss German sentence.

Also note that URLs that have never been visited can also be stored in the `urls` collection. They will be
updated or moved to the `blacklist` after the first visit.
"""

from datetime import datetime

from mongoengine import *

from .generic import Source, CrawlMeta


class AbstractMongoURL(Document):
    """
    An abstract :py:class:`mongoengine.Document` for *interesting* URLs, stored in the ``urls`` collection.

    .. todo:
        Also keep track of how many sentences and Swiss German sentences were found during a crawl ?
        For that, one suggestion is to change the :py:attr:`crawl_history` entries from date and count to
        date, new_count, sg_count, sentence_count.
    """

    id = StringField(primary_key=True)
    """The URL, also used as a primary key."""

    source = EmbeddedDocumentField(Source, default=Source())
    """The source of the URL (see :py:class:`~swisstext.mongo.abstract.generic.Source`). 
    Possible sources are defined in :py:class:`~swisstext.mongo.abstract.generic.SourceType`."""

    date_added = DateTimeField(default=lambda: datetime.utcnow())
    """When the URL was added to the collection, in UTC."""

    crawl_history = EmbeddedDocumentListField(CrawlMeta, default=[])
    """One entry for each visit of this URL by the scraper, ordered by the visit date ascending."""

    count = IntField(default=0)
    """
    Total number of new sentences found on this page in all visit.
    
    .. code-block:: python 
    
        AbstractMongoURL.count == sum((ch.count for ch in AbstractMongoURL.crawl_history))
        
    """
    delta = IntField(default=0)
    """The number of new sentences found on the last visit (same as ``crawl_history[-1].count``)."""

    delta_date = DateTimeField(default=None)
    """The date of the last visit (same as ``crawl_history[-1].date``). Inexistant if the URL was never crawled."""

    meta = {'collection': 'urls', 'abstract': True}

    @classmethod
    def exists(cls, url) -> bool:
        """Test if a URL exists."""
        return cls.objects.with_id(url) is not None

    @classmethod
    def create(cls, url, source=Source()) -> Document:
        """
        Create a URL. *Warning*: this **won't save** the document automatically.
        You need to call the ``.save`` method to persist it into the database.
        """
        return cls(id=url, source=source)

    @classmethod
    def get(cls, url) -> object:
        """Get a URL Document instance by ID."""
        return cls.objects.with_id(url)

    @classmethod
    def get_never_crawled(cls) -> QuerySet:
        """Get a :py:class:`~mongoengine.queryset.QuerySet` of URLs that have never been visited."""
        return cls.objects(crawl_history__size=0)

    @classmethod
    def try_delete(cls, url: str):
        """Delete a URL if it exists. Otherwise, do nothing silently."""
        # remove from url if it exists
        cls.objects(id=url).delete()

    def add_crawl_history(self, new_sg_count):
        """
        Add a crawl history entry. Note that this will update the document instance,
        but won't persist the change to mongo. You need to call :py:meth:`mongoengine.Document.save` yourself.

        :param new_sg_count: the number of new sentences found on this crawl.
        :return: self
        """
        meta = CrawlMeta(count=new_sg_count)
        self.crawl_history.append(meta)
        self.count += new_sg_count
        self.delta = meta.count
        self.delta_date = meta.date
        # don't call self.save, as this method is often called alongside other updates to the document
        return self  # for chaining


class AbstractMongoBlacklist(Document):
    """An abstract :py:class:`mongoengine.Document` for *uninteresting* URLs, stored in the ``blacklist`` collection."""

    url = StringField(primary_key=True)
    """The blacklisted URL, acting as a primary key."""

    date_added = DateTimeField(default=lambda: datetime.utcnow())
    """When the URL was added to the blacklist"""

    source = EmbeddedDocumentField(Source, default=Source())
    """What/who triggered the blacklisting, see :py:class:`swisstext.mongo.abstract.generic.Source`."""
    meta = {'collection': 'blacklist', 'abstract': True}

    @classmethod
    def exists(cls, url) -> bool:
        """Test if a url is blacklisted."""
        return cls.objects.with_id(url) is not None

    @classmethod
    def add_url(cls, url: str, source: Source = None):
        """
        Blacklist a URL. This will create and save the entry to mongo automatically.

        .. note:
            It is important to ensure a URL is not present in both the `urls` and the `blacklist` collection.
            To avoid this discrepancy, call :py:meth:`AbstractMongoSentence.try_delete` first.
        """
        # add it to the blacklist
        cls(
            url=url,
            source=source or Source()
        ).save()
