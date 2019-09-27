"""
This module defines interfaces for each tool or decision maker used in the searching process.
This makes it easy to test new ways or to tune one aspect of the search engine while keeping most of the code unchanged.

See the :py:mod:`swisstext.cmd.searching.tools` module for implementations.
"""

from abc import ABC, abstractmethod
from typing import Iterable, List

from .data import Seed
import itertools


class ISearcher(ABC):
    """
    [ABSTRACT] This tool is the core of the pipeline: it is an interface to a real search engine.
    """

    @abstractmethod
    def search(self, query) -> Iterable[str]:
        """
        [ABSTRACT] Should query a real search engine and returns an iterator of results/URLs.
        The use of an iterator allows for lazy implementations, in case we are limited by an API quota.
        """
        pass

    def top_results(self, query, max_results=10) -> List:
        """
        Use the :py:meth:`search` to return the x top results for a query.
        """
        return list(itertools.islice(self.search(query), max_results))


class IQueryBuilder:
    """
    Do some preprocessing on the query before submitting it to a search engine.
    The builder can be used to prepare a query from a seed, such as quoting words, using "AND" keywords, etc.
    """

    def prepare(self, query: str, **kwargs):
        """By default, does nothing."""
        return query


class ISaver(ABC):
    """
    [ABSTRACT] The saver is responsible for persisting everything somewhere, such as a database, a file or the console.
    """

    @abstractmethod
    def save_seed(self, seed: Seed):
        """[ABSTRACT] Should persist a seed and its associated results."""
        pass

    def link_exists(self, url: str) -> bool:
        """Test if the url already exists in the persistence layer. Returns false by default."""
        return False
