"""
Class representing a ``seed`` entry in the MongoDatabase.

A seed is a string used as a search engine query in order to find new Swiss German URLs. In the SwissText system,
seeds can be added by users or generated automatically. Each seed will potentially be used multiple times.

Seeds are generated automatically in :mod:`swisstext.cmd.crawling` and used in :mod:`swisstext.cmd.searching`. Users
can also add seeds manually to the collection using the Frontend (see :mod:`swisstext.frontend`).
"""
from datetime import datetime

from mongoengine import *
from .generic import CrawlMeta, Source, Deleted


class AbstractMongoSeed(Document):
    """An abstract :py:class:`mongoengine.Document` for a seed, stored in the ``seeds`` collection."""

    ##-- base info

    id = StringField(primary_key=True)
    """The seed itself is used as an primary key to avoid duplicates.
    
    .. note:: 
        only true duplicates are detected, so ensure the seed is lowercase and trimed before insert. 
    """

    source = EmbeddedDocumentField(Source, default=Source())
    """
    Source of the seed. Possible values are:
    
    * ``SourceType.AUTO`` or ``SourceType.UNKNOWN``: no extra required,
    * ``SourceType.USER``: the extra is the id of the user.
    """

    date_added = DateTimeField(default=lambda: datetime.utcnow())
    """When the seed has been added to the collection, in UTC."""

    ##-- seed usage

    count = IntField(default=0)
    """The number of new URLs found. This counter is incremented on each seed use for any new URL, whether the 
    URL is actually a "good URL" (i.e. really contains Swiss German) or not. This is because to determine the
    quality of a URL, one need to actually crawl it. """

    delta_date = DateTimeField()
    """Date of the last use of this seed in a search."""

    search_history = EmbeddedDocumentListField(CrawlMeta, default=[])
    """A list of usage. For each use, we record the date and the number of new URLs found. The sum of each
    search history ``count`` should be equal to the ``count`` variable. """

    ##-- deletion
    deleted = EmbeddedDocumentField(Deleted)
    """
    This field is only present in the collection if the seed has been deleted. Use the following query
    to get deleted seeds:
    
    .. code-block:: javascript
    
        db.seeds.find({deleted: {$exists: true})
        
    """
    meta = {'collection': 'seeds', 'abstract': True}

    @classmethod
    def get(cls, seed):
        """Get a seed by ID."""
        return cls.objects.with_id(seed)

    @classmethod
    def create(cls, seed, source=Source()):
        """
        Create a seed. *Warning*: this **won't save** the document automatically.
        You need to call the ``.save`` method to persist it into the database.

        :param seed: the seed
        :param source: the source of the seed, default to ``SourceType.UNKNOWN``
        """
        return cls(id=seed, source=source)

    @classmethod
    def exists(cls, text) -> bool:
        """
        Test if a seed already exists.

        :param text: the seed
        """
        return cls.objects.with_id(text) is not None

    def add_search_history(self, new_links_count):
        """Add a search history entry. This should be call after each usage of the seed.

        :param new_links_count: the number of new URLs found.
        """
        entry = CrawlMeta(count=new_links_count)
        self.count += new_links_count
        self.delta_date = entry.date
        self.search_history.append(entry)

    @classmethod
    def find_similar(cls, seed):
        """
        Find similar seeds. Currently, this method is quite *dumb*: it will search for seeds containing one or
        more words present in `seed` using regex.

        .. note:: the actual regex for a seed like *hello world* will use the regex ``(hello)|(world)``, so
                  a seed like *worldnews* may also be included in the results.

        :param seed: the seed to search for
        :return: a :class:`mongoengine.BaseQuery` object for other seeds containing similar words.
        """
        import re
        split = re.split('\s+', seed)
        if len(split) == 1:
            return cls.objects(id__icontains=seed)
        else:
            pattern = "(%s)" % ")|(".join(split)
            return cls.objects(id=re.compile(pattern, re.IGNORECASE))

    @classmethod
    def mark_deleted(cls, obj, uuid, comment=None):
        """
        Mark one or multiple seeds as deleted.

        :param obj: either a seed ID (i.e. a string), a ``MongoSeed`` instance or a ``QuerySet`` of seeds.
        :param uuid: the ID of the user deleting the seed.
        :param comment: an optional comment
        """
        if isinstance(obj, str): obj = cls.objects.with_id(obj)
        obj.update(set__deleted=Deleted(by=uuid, comment=comment))

    @classmethod
    def unmark_deleted(cls, obj):
        """
        Undelete a seed. This will *unset* the ``deleted`` flag completely. In Mongo Shell, use:

        .. code-block:: javascript

            db.seeds.find({_id: "the seed"}, {$unset: {deleted_by:1}})

        :param obj: either a seed ID (i.e. a string), a ``MongoSeed`` instance or a ``QuerySet`` of seeds.
        """
        if isinstance(obj, str): obj = cls.objects.with_id(obj)
        obj.update(unset__deleted=True)
