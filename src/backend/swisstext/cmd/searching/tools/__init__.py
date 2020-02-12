"""
This package contains various implementations of the different search engine tools.

.. seealso::

    :py:mod:`~swisstext.cmd.searching.interfaces`
        The tools interfaces definitions

    :py:mod:`~swisstext.cmd.searching.config`
        The default configuration instantiates tools from this package
"""

from .google_search import GoogleGeneratorFactory
from .start_page import StartPageGeneratorFactory

from .console_saver import ConsoleSaver
from .mongo_saver import MongoSaver

from .builders import QuoteQueryBuilder, QuoteWordsQueryBuilder