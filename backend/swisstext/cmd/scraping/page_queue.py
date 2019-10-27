import logging
from queue import Queue
from threading import Lock
from typing import Set

from .data import Page

logger = logging.getLogger(__name__)


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
        to correctly filter child URLs (using for example :py:mod:`~swisstext.cmd.link_utils`)?
    """

    lock = Lock()

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

        url = page.url
        try:
            self.lock.acquire() # better safe than sorry...
            if url not in self.uniq:
                self.uniq.add(url)
                super()._put((page, depth))
        finally:
            self.lock.release()
