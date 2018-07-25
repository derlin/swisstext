from collections import OrderedDict

from mongoengine import *
from datetime import datetime

from .users import AbstractMongoUser

# Dialects = OrderedDict(
#     ba_sn="Basel, Solothurn Nord",
#     ss_bn="Solothurn Süd, Bern Nord",
#     bo_fr="Berner Oberland, Freiburg",
#     walli="Wallis",
#     a_l_z="Aargau, Luzern, Zug Nord",
#     zuric="Zürich",
#     nords="Nordostschweiz (SH, TG, SG Nord, AR, AI)",
#     zentr="Zentralschweiz (OW, NW, UR, SZ, ZG Süd)",
#     g_sgs="Glarus und SG Süd",
#     graub="Graubünden"
# )

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


class SourceType:
    UNKNOWN = "unknown"
    USER = "user"
    AUTO = "auto"
    SEED = "seed"


class Source(EmbeddedDocument):
    type_ = StringField(db_field='type', default=SourceType.UNKNOWN)
    extra = StringField()


class CrawlMeta(EmbeddedDocument):
    date = DateTimeField(default=lambda: datetime.utcnow())
    count = IntField(default=0)


class Deleted(EmbeddedDocument):
    by = AbstractMongoUser._id_type()
    comment = StringField()
    date = DateTimeField(default=lambda: datetime.utcnow())
