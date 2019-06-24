"""
This module contains multiple :py:class:`~swisstext.cmd.scraping.interfaces.IDecider` implementations.
"""
import logging
from datetime import datetime, timedelta

from pytimeparse.timeparse import timeparse

from ..data import Page
from ..interfaces import IDecider

ABSOLUTE_MIN_RECRAWL_DELTA = timedelta(seconds=timeparse("4d"))
MIN_RECRAWL_DELTA = "7d"
MIN_RATIO = 0

logger = logging.getLogger(__name__)


class BasicDecider(IDecider):
    """
    A basic decider that:

    * crawls URLs that fulfill one of the following criteria:

        * the URL is new,
        * the last visit yielded at least one new sentence on the last visit,
        * the last visit was older than :py:attr:`min_recrawl_delta`

    * blacklists URLs with no Swiss German sentences,
    * adds child URLs from a page only if the ratio between sentences and Swiss German sentences is greater or
      equal :py:attr:`min_ratio`
    """

    def __init__(self, min_ratio=MIN_RATIO, min_recrawl_delta: str = None, **kwargs):
        """
        :param min_ratio: the min ratio
        :param min_recrawl_delta: a string that can be parsed to a time difference using ``pytimeparse.timeparse``
        """
        self.min_ratio = min_ratio  #: Child URLs are added only if sentence_count / sg_count > min_ratio
        delta_sec = None
        if min_recrawl_delta is not None:
            try:
                delta_sec = timeparse(min_recrawl_delta)
            except:
                logger.warning(f'Could not parse min_recrawl_delta ({min_recrawl_delta}). Using default.')
        if delta_sec is None:
            delta_sec = timeparse(MIN_RECRAWL_DELTA)

        self.min_recrawl_delta = timedelta(seconds=delta_sec)  #: a timedelta. URLs are revisited if now() - last visit > min_recrawl_delta (UTC)

    def should_page_be_crawled(self, page: Page) -> bool:
        """
        Returns true if the URL is new,
        or the page's :py:attr:`~..data.Page.delta_count` above 0 and
        the page's `:py:attr:~..data.Page.delta_date` is older than :py:attr:`min_recrawl_delta`
        note that a page will NEVER be recrawled if the last crawl is less than ABSOLUTE_MIN_RECRAWL_DELTA old.
        """
        if page.is_new(): return True

        delta = datetime.utcnow() - page.score.delta_date
        return delta > ABSOLUTE_MIN_RECRAWL_DELTA \
            if page.score.delta_count > 0 \
            else delta > self.min_recrawl_delta

    def should_children_be_crawled(self, page: Page) -> bool:
        """
        Returns true if
        the page's :py:attr:`~swisstext.cmd.scraping.data.Page.sg_count` is above 0 and
        :py:attr:`~..data.Page.sentence_count` /
        :py:attr:`~..data.Page.sg_count` >= :py:attr:`min_ratio`"""
        # TODO: use new_count vs sg_count ?
        return page.sg_count > 0 and page.sentence_count / page.sg_count > self.min_ratio

    def should_url_be_blacklisted(self, page: Page) -> bool:
        """Returns true only if the URL is new (first visit) and no Swiss German sentence is present in the page."""
        return page.is_new() and page.sg_count == 0


class OnlyNewDecider(BasicDecider):
    """
    Same as :py:class:`BasicDecider`, but only crawls new URLs.
    """

    def should_page_be_crawled(self, page: Page) -> bool:
        """Returns true only if the page is new."""
        return page.is_new()
