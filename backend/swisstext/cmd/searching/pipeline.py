"""
This module contains the core of the searching system.
"""

from typing import List

from ..link_utils import filter_links, fix_url
from .data import Seed
from .interfaces import IQueryBuilder, ISearcher, ISaver

import logging

logger = logging.getLogger(__name__)


class SearchEngine:
    """
    The search engine implements all the logic of searching seeds and persisting results.

    Note that this class is usually instantiated by a :py:class:`~swisstext.cmd.searching.config.Config` object.
    """

    def __init__(self, query_builder: IQueryBuilder, searcher: ISearcher, saver: ISaver):
        self.query_builder = query_builder
        self.searcher = searcher
        self.saver = saver
        self.new_urls = set()  #: the list of URLs discovered during the lifetime of the object

    def process(self, seeds: List[Seed], **kwargs) -> int:
        """
        Do the magic.

        Note that this method was not been implemented with multithreading in mind, as most of the time
        search engine APIs are limited and pretty fast...
        """
        new_count = 0
        for seed in seeds:
            new_count += self.process_one(seed, **kwargs)
        return new_count

    def process_one(self, seed, max_results=10, max_fetches=-1):
        query = self.query_builder.prepare(seed.query)
        links_counter = 0

        logger.debug(f"Searching seed='{seed.query}', query='{query}'")

        for raw_counter, raw_link in enumerate(self.searcher.search(query)):
            # "fix" the URL we got
            link, ok = fix_url(raw_link)
            if not ok:
                # the link is "blacklisted"
                logger.debug(f' NOT OK: {link}')
            elif self.saver.link_exists(link):
                # the link is already in the DB
                logger.debug(f'    DUP: {link}.')
            else:
                # got a new link !! save it
                logger.debug(f'  SAVED: {link}.')
                seed.new_links.append(link)
                self.new_urls.add(link)
                links_counter += 1

                if links_counter >= max_results:
                    # don't pull more than the given limit
                    logger.debug(f'reached max results {max_results}.')
                    break


            if max_fetches > 0 and raw_counter >= max_fetches:
                logger.debug(f'reached max fetches {max_fetches}.')
                # we didn't get as many results as expected,
                # but we stop anyhow (hence avoid too many API calls)
                break

        self.saver.save_seed(seed)
        return links_counter

    def _process_(self, seeds: List[Seed], max_results=10):
        """
        Do the magic.

        Note that this method was not been implemented with multithreading in mind, as most of the time
        search engine APIs are limited and pretty fast...
        """
        added_urls = 0
        for seed in seeds:
            for link in filter_links('', self.searcher.top_results(seed.query, max_results)):
                if link not in self.new_urls:
                    if not self.saver.link_exists(link):
                        seed.new_links.append(link)
                        added_urls += 1
                    self.new_urls.add(link)
            self.saver.save_seed(seed)
        return added_urls
