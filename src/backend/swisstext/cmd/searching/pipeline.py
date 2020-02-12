"""
This module contains the core of the searching system.
"""

from typing import List, Tuple

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

    def process_one(self, seed: Seed, max_results=10, max_fetches=-1) -> int:
        """
        Process one seed. Note that if called multiple times, the previous results
        are still saved in :py:attr:`SearchEngine.new_urls` so duplicate URLs will be skipped.

        :param seed: the seed to search for
        :param max_results: the target number of URLs to find
        :param max_fetches: the maximum number of URLs fetched from the search engine
        :return: a list of URLs, with 0 <= length <= max_results
        """
        query = self.query_builder.prepare(seed.query)
        links_counter = 0

        logger.info(f"Searching seed='{seed.query}', query='{query}'")

        for raw_counter, raw_link in enumerate(self.searcher.search(query)):
            # check the link first
            link, ok = self.check_link(raw_link)

            if ok:
                # == got a new link !! save it
                seed.new_links.append(link)
                self.new_urls.add(link)
                links_counter += 1

                # == check the end of iterations
                if links_counter >= max_results:
                    # don't pull more than the given limit
                    logger.debug(f'reached max results {max_results}.')
                    break
                if max_fetches > 0 and raw_counter >= max_fetches:
                    logger.debug(f'reached max fetches {max_fetches}.')
                    # we didn't get as many results as expected,
                    # but we stop anyhow (hence avoid too many API calls)
                    break

        self.saver.save_seed(seed, was_used=True)
        logger.info(f"  found {len(seed.new_links)} new URLs.")
        return links_counter

    def check_link(self, raw_link: str) -> Tuple[str, bool]:
        """
        Potentially "fix" the url (see :py:mod:`~swisstext.cmd.link_utils`) and check that
        is is unique (not found on a previous search with this instance and not already present
        in the backend). Turn on debug to follow what is going on.

        :param raw_link: the raw URL (must be absolute)
        :return: a tuple with the fixed URL and a "ok" flag
        """
        # "fix" the URL we got
        link, ok = fix_url(raw_link)

        # == first basic checks
        if not ok:
            # the link is "blacklisted" by the link_utils module
            logger.debug(f'  NOT OK: {link}')
        elif link in self.new_urls:
            # the link is already in the previous results
            logger.debug(f'     DUP: {link}.')
        else:
            # == query the saver
            status = self.saver.link_exists(link)
            if status == ISaver.LinkStatus.BLACKLISTED:
                # the link has been blacklisted
                logger.debug(f' BLCKLST: {link}.')
            elif status == ISaver.LinkStatus.EXISTS:
                # the link is already in the DB
                logger.debug(f'   DUP_S: {link}.')
            else:
                # all checks are preformed
                logger.debug(f'   SAVED: {link}.')
                return link, True

        return link, False
