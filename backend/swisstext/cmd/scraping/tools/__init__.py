"""
This package contains various implementations of the different pipeline tools.

.. seealso::

    :py:mod:`~swisstext.cmd.scraping.interfaces`
        The tools interfaces definitions

    :py:mod:`~swisstext.cmd.scraping.config`
        The default configuration instantiates tools from this package
"""

# deciders
from .basic_decider import BasicDecider
# seed creators
from .basic_seed_creator import BasicSeedCreator, IdfSeedCreator
# crawlers
from .bs_crawler import BsCrawler, CleverBsCrawler
from .justext_crawler import JustextCrawler
# splitters
from .mocy_splitter import MocySplitter
from .moses_splitter import MosesSplitter
from .punkt_splitter import PunktSplitter
# sentence filters
from .pattern_sentence_filter import PatternSentenceFilter
# savers
from .console_saver import ConsoleSaver
from .mongo_saver import MongoSaver
# language id
from .swigspot_langid import SwigspotLangid