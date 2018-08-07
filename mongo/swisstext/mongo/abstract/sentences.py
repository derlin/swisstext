"""
Classes for interacting with a Swiss German ``sentence`` in the MongoDatabase.

Sentences are unique and found automatically using the swisstext crawler (see :mod:`swisstext.cmd.scraping`).
Once a sentence is added to the collection, it is never deleted, except if the URL it comes from is blacklisted.

Using the SwissText Frontend (see :mod:`swisstext.frontend`), users can:

* validate the sentence: i.e. mark it as actually Swiss German,
* label the sentence: assign a dialect (see :class:`DialectInfo`) to it,
* delete a sentence: this will just add a deleted flag, not actually remove the sentence from the collection.
"""

from cityhash import CityHash64
from datetime import datetime

from mongoengine import *

from .generic import Deleted
from .users import AbstractMongoUser


class DialectEntry(EmbeddedDocument):
    """Represents a *vote*, i.e. dialect label, assigned by a user. """
    user = StringField()
    """The ID of the user"""
    label = StringField()
    """The label (see :py:const:`swisstext.mongo.abstract.generic.Dialects` for a list of available labels)"""
    date = DateTimeField(default=lambda: datetime.utcnow())
    """The date of the vote, in UTC"""


class DialectInfo(EmbeddedDocument):
    """
    A :py:class:`mongoengine.EmbeddedDocument` that Encapsulates all the dialect-tagging information for a sentence.

    Usually, a sentence will be presented to a given user only once. If the user knows the dialect, an
    entry in :py:attr:`labels` is added. If the user doesn't know, his ID is added to :py:attr:`skipped_by`.
    Thus, a user ID should be present *at most* in one of the two lists.

    The current dialect is stored in :py:attr:`label`. In order to judge the pertinence of the former,
    two statistics can be used: :py:attr:`count` is the total number of users having voted for the label,
    while :py:attr:`confidence` is the ratio between the number of votes for this label and the total number of votes.


    .. warning::
        Most of the methods here call :py:meth:`mongoengine.EmbeddedDocument.save` under the hood, thus persisting
        the changes automatically to the DB.

        This usually works fine, but this means you CAN NOT manipulate a
        ``DialectInfo`` instance if it is not attached to a :py:class:`mongoengine.Document`.

        Moreover, you can sometimes run into a
        ':py:class:`ReferenceError`: *weakly-referenced object no longer exists'*
        (only when using Flask-Mongoengine ?). If this is the case, ensure that you have a strong reference to the
        parent document in your code. Here is an example:

        .. code-block:: python

            # let's say MongoSentence implements AbstractMongoSentence
            # This can raise a ReferenceException:
            MongoSentence.objects.with_id(sid).dialect.add_label(uuid, label)
            # while this is fine:
            s = MongoSentence.objects.with_id(sid)
            s.dialect.add_label(uuid, label) # OK
    """

    label = StringField()
    """
    Current label, i.e. the label with the highest number of votes. 
    In case of a draw, one label is selected randomly. This is why the :py:attr:`confidence` information
    is important.
    """

    count = IntField()
    """Number of people that voted for the current label."""

    confidence = FloatField()
    """Defined by ``count / len(labels)``. Gives a rough estimate of how "*good*" a label is."""

    labels = EmbeddedDocumentListField(DialectEntry, default=[])
    """All the votes, as a list of  :py:class:`DialectEntry`."""

    skipped_by = ListField(AbstractMongoUser._id_type(), default=[])
    """A list of User ID, corresponding to users having seen the sentence, but were not able to label it."""

    def get_label_by(self, uuid) -> str:
        """
        Get the label given by a user.

        :param uuid: the user ID
        :return: the label as a string, or None if the user hasn't labelled the sentence.
        """
        entry = [l for l in self.labels if l.user == uuid]
        return None if len(entry) == 0 else entry[0].label

    def add_label(self, uuid, label):
        """
        Add a label and save the document. Note the following two special cases:
        1. the user has already voted: the old vote will be deleted / replaced
        2. the user has previously skipped the sentence: the user ID will be removed from :py:attr:`skipped_by`

        :param uuid: the user ID
        :param label: the label
        :return: self
        """
        if label:  # ensure the label exists
            self.remove_label(uuid)  # ensure not duplicates
            self.labels.append(DialectEntry(user=uuid, label=label))
            self._recompute_label()
            self.save()
        return self

    def remove_label(self, uuid):
        """
        Remove the label from a user and save the change to MongoDb.
        Note that it does nothing if the user didn't vote.

        :param uuid: the user ID
        :return: self
        """
        label = self._get_label_entry(uuid)
        if label:
            self.labels.remove(label)
            self._recompute_label()
            self.save()
        return self

    def skip(self, uuid):
        """
        Add the user to the :py:attr:`skipped_by` list. Note that if the user already voted, his vote will be removed
        from :py:attr:`labels` to ensure consistency.

        :param uuid: the user ID
        :return: self
        """
        if uuid not in self.skipped_by:
            self.remove_label(uuid)
            self.skipped_by.append(uuid)
            self.save()
        return self

    def unskip(self, uuid):
        """
        Remove a user from the :py:attr:`skipped_by` list.

        :param uuid: the user ID
        :return: self
        """
        if uuid in self.skipped_by:
            self.skipped_by.remove(uuid)
            self.save()
        return self

    def _get_label_entry(self, uuid) -> str:
        # get the LabelInfo instance for a given user, or None if the user didn't vote.
        entry = [l for l in self.labels if l.user == uuid]
        return None if len(entry) == 0 else entry[0]

    def _recompute_label(self):
        # recompute the current label and its statistics after a change.
        if self.labels:
            sums = {}
            for l in self.labels:
                sums.setdefault(l.label, 0)
                sums[l.label] += 1
            self.label, self.count = sorted(sums.items(), key=lambda t: -t[1])[0]
            self.confidence = self.count / len(self.labels)
        else:
            # mmh... not ideal to have None values, but it is not possible
            # to remove the DialectInfo entry from here
            self.label = None
            self.count, self.confidence = 0, .0


class AbstractMongoSentence(Document):
    """
    An abstract :py:class:`mongoengine.Document` for a sentence, stored in the ``sentence`` collection.

    To avoid duplicates, the primary key is a hash derived from the text. We currently use
    `CityHash64 <https://opensource.googleblog.com/2011/04/introducing-cityhash.html>`_, a hashing function
    especially made for hashtables instead of cryptography. Note that the hash is case-sensitive and that
    the text should be trimed before hashing (by calling :py:meth:`string.trim` for example).
    There is also no guarantee that there won't be clashes.
    """

    # -- base info
    id = StringField(primary_key=True)
    """The sentence ID, computed by hashing the text using :py:meth:`get_hash`."""

    text = StringField()
    """The raw text, without any transformations except trim."""

    url = StringField()
    """The source URL."""

    # -- crawl info
    date_added = DateTimeField(default=lambda: datetime.utcnow())
    """The date when the sentence was added to the collection, in UTC."""

    crawl_proba = FloatField()
    """The probability of Swiss German, as calculated by the LID model during crawl."""

    # -- validation info
    validated_by = ListField(AbstractMongoUser._id_type(), default=[])
    """A list of user ID that have seen the sentence and validated it as Swiss German in the Frontend."""

    deleted = EmbeddedDocumentField(Deleted)
    """A deleted flag (with date, user ID and optional comment) that exists only if the sentence is deleted."""

    # -- dialect info
    dialect = EmbeddedDocumentField(DialectInfo)
    """All the informations about dialect tagging (see :py:class:`DialectInfo`). 
    Note that this field can be absent (never labelled by anyone) or its label empty (all labels removed)."""

    meta = {'collection': 'sentences', 'abstract': True}

    @classmethod
    def add_label(cls, obj, uuid, label, **kwargs):
        """
        Add a dialect label. This method first ensures that the :py:attr:`dialect` attribute is not null, then
        forwards the call to :py:meth:`DialectInfo.add_label`.

        :param obj: either the ID of a sentence (a string) or an actual sentence.
        :param uuid: the ID of the user labelling the sentence.
        :param label: the label (see :py:const:`~swisstext.mongo.abstract.generic.Dialects`)
        """
        if isinstance(obj, str): obj = cls.objects.with_id(obj)
        if isinstance(obj, cls):
            if obj.dialect is None: obj.dialect = DialectInfo()
            obj.dialect.add_label(uuid, label)

    @classmethod
    def remove_label(cls, obj, uuid):
        """
        Remove a label added by a user. This method just forwards the call to :py:meth:`DialectInfo.add_label`.

        :param obj: either the ID of a sentence (a string) or an actual sentence.
        :param uuid: the ID of the user for which to remove the label.
        """
        if isinstance(obj, str): obj = cls.objects.with_id(obj)
        if isinstance(obj, cls):
            obj.dialect.remove_label(uuid)

    @classmethod
    def exists(cls, text) -> bool:
        """Test if a sentence already exists (case sensitive)."""
        return cls.objects(id=cls.get_hash(text)).count() == 1

    @classmethod
    def create(cls, text, url, proba):
        """
        Create a seed. *Warning*: this **won't save** the document automatically.
        You need to call the ``.save`` method to persist it into the database.
        """
        return cls(id=cls.get_hash(text), text=text, url=url, crawl_proba=proba)

    @staticmethod
    def get_hash(text) -> str:
        """Hash the given text using
        `CityHash64 <https://opensource.googleblog.com/2011/04/introducing-cityhash.html>`_. """
        return str(CityHash64(text))

    @classmethod
    def mark_deleted(cls, obj, uuid, comment=None):
        """
        Mark a sentence as deleted.

        :param obj: either the ID of a sentence (a string) or an actual sentence.
        :param uuid: the ID of the user deleting the sentence.
        :param comment: an optional comment.
        """
        if isinstance(obj, str): obj = cls.objects.with_id(obj)
        obj.update(set__deleted=Deleted(by=uuid, comment=comment))

    @classmethod
    def unmark_deleted(cls, obj):
        """
        Restore a deleted sentence.

        :param obj: either the ID of a sentence (a string) or an actual sentence.
        """
        # in mongo shell, use $unset:
        # sentences.find({_id: xxx}, {$unset: {deleted_by:1}})
        if isinstance(obj, str): obj = cls.objects.with_id(obj)
        obj.update(unset__deleted=True)
