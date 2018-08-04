"""
Define generic/reused embedded documents as well as constants.
"""

from collections import OrderedDict

from mongoengine import *
from datetime import datetime

from .users import AbstractMongoUser

Dialects = OrderedDict(
    ba_sn="Basel, Solothurn Nord",
    zuric="Zürich",
    ss_bn="Solothurn Süd, Bern Nord",
    nords="Nordostschweiz (SH, TG, SG Nord, AR, AI)",
    bo_fr="Berner Oberland, Freiburg",
    zentr="Zentralschweiz (OW, NW, UR, SZ, ZG Süd)",
    walli="Wallis",
    g_sgs="Glarus und SG Süd",
    a_l_z="Aargau, Luzern, Zug Nord",
    graub="Graubünden"
)
"""
An ordered dictionary of available dialect tags.
The dialect tags come from the Master Thesis of Sandra Kellerhals,
"*Dialektometrische Analyse und Visualisierung von schweizerdeutschen Dialekten auf verschiedenen linguistischen Ebenen*",
p. 62 (see category *Alle SDS- und SADS- Daten 10 Dialektregionen*)
"""


class SourceType:
    """
    Possible sources for a URL or a Seed.
    """
    UNKNOWN = "unknown"  #: This is used when the seeds/urls are read from a file
    USER = "user"  #: When user is set, the source.extra should contain the user id
    AUTO = "auto"  #: Auto means it has been generated automatically by the system during regular execution
    SEED = "seed"  #: The URL was found by searching the seed whose ID figures in source.extra


class Source(EmbeddedDocument):
    """
    A source field. It contains two informations:
    :py:attr:`type_` (mapped to `type` in mongo), one of the :class:`SourceType` above and
    :py:attr:`extra` for an optional extra information.

    If the source is attached to a URL, possible values are:
        * ``(SourceType.UNKNOWN, None)``
        * ``(SourceType.USER, "user ID")``
        * ``(SourceType.SEED, "seed ID")``
        * ``(SourceType.AUTO, "parent url")``

    If the source is attached to a Seed, possible values are:
        * ``(SourceType.UNKNOWN, None)``
        * ``(SourceType.USER, "user ID")``
        * ``(SourceType.AUTO, None)``
    """
    type_ = StringField(db_field='type', default=SourceType.UNKNOWN)
    extra = StringField()


class CrawlMeta(EmbeddedDocument):
    """ Holds a date and a count of items """
    date = DateTimeField(default=lambda: datetime.utcnow())
    """The creation/added date, in UTC."""
    count = IntField(default=0)
    """Items count, for example the number of new URLs found."""


class Deleted(EmbeddedDocument):
    """ A deleted flag. """
    by = AbstractMongoUser._id_type()
    """The ID of the user triggering deletion, required !"""
    comment = StringField()
    """Optional, not recorded to the DB if not specified"""
    date = DateTimeField(default=lambda: datetime.utcnow())
    """The datetime, generated automatically on creation in UTC"""
