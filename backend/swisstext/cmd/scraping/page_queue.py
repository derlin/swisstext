import logging
from queue import Queue
from typing import Set

from .data import Page

logger = logging.getLogger(__name__)

EXCLUDE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'pdf']


class PageQueue(Queue):
    """
    A :py:class:`~queue.Queue` that ensures enqueued pages are unique and not clearly pointing to images or PDFs
    (i.e. ending with .jpg, .jpeg, .png or .pdf).

    Elements in the queue should be **tuples**, with the first element a :py:class:`~Page` and the second the
    crawl depth (as int)

    .. todo:

        Is the excluded_extensions really useful here ?

        Should we also check here that the URL is interesting or do we trust
        :py:class:`~swisstext.cmd.scraping.interfaces.ICrawler` implementations
        to correctly filter child URLs (using for example :py:mod:`~swisstext.cmd.scraping.link_utils`)?
    """

    def _init(self, maxsize):
        super()._init(maxsize)
        self.uniq: Set[Page] = set()

    def _put(self, tup):
        if type(tup) is Page:
            page, depth = tup, 1
            logger.warning(f"The element to enqueue is missing depth information: '${tup}'. Set depth to 1.")
        else:
            assert type(tup) is tuple
            page, depth = tup
            assert isinstance(page, Page)

        if self._should_be_added(page.url):
            super()._put((page, depth))

    def _should_be_added(self, url):
        # url = url[:url.index("#")] if "#" in url else url
        if url in self.uniq or url.split(".")[-1].lower() in EXCLUDE_EXTENSIONS:
            return False
        else:
            self.uniq.add(url)
            return True
