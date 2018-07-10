import logging
from queue import Queue
from typing import Set

from swisstext.page import Page

logger = logging.getLogger(__name__)

EXCLUDE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'pdf']


class PageQueue(Queue):

    def _init(self, maxsize):
        super()._init(maxsize)
        self.uniq: Set[Page] = set()

    def _put(self, tup):
        page, depth = tup
        if self._should_be_added(page.url):
            super()._put(tup)

    def _should_be_added(self, url):
        # url = url[:url.index("#")] if "#" in url else url
        if url in self.uniq or url.split(".")[-1].lower() in EXCLUDE_EXTENSIONS:
            return False
        else:
            self.uniq.add(url)
            return True
