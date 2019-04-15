"""
This module contains the core of the searching system.
"""

from typing import List

from ..link_utils import is_url_interesting
from .data import Seed
from .interfaces import ISearcher, ISaver


class SearchEngine:
    """
    The search engine implements all the logic of searching seeds and persisting results.

    Note that this class is usually instantiated by a :py:class:`~swisstext.cmd.searching.config.Config` object.
    """
    def __init__(self, searcher: ISearcher, saver: ISaver):
        self.searcher = searcher
        self.saver = saver
        self.new_urls = set() #: the list of URLs discovered during the lifetime of the object

    def process(self, seeds: List[Seed], max_results=10):
        """
        Do the magic.

        Note that this method has not been implemented having multithreading in minds, as most of the time
        search engine APIs are limited and pretty fast...
        """
        added_urls = 0
        for seed in seeds:
            for link in self.searcher.top_results(seed.query, max_results):
                if is_url_interesting(link) and link not in self.new_urls:
                    if not self.saver.link_exists(link):
                        seed.new_links.append(link)
                        added_urls += 1
                    self.new_urls.add(link)
            self.saver.save_seed(seed)
        return added_urls