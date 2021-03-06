from multiprocessing import Lock

from ..interfaces import ISaver
from ..data import Page, PageScore
import logging

logger = logging.getLogger(__name__)


class ConsoleSaver(ISaver):
    """
    Implementation of an :py:class:`~swisstext.cmd.scraping.interfaces.ISaver` useful for testing and debugging.
    It does not persist any results, but prints everything to the console instead.

    Blacklisted URLs and sentences are kept in sets in memory.
    """

    def __init__(self, sentences_file: str = None, **kwargs):
        """
        :param sentences_file: optional path to a file were new sentences are written.
            Note that the file is overriden on each run.
        """
        super().__init__()
        self._blacklist = set()
        self._sentences = set()
        self._pages = dict()
        self._saved_urls = set()
        self.sfile = None

        if sentences_file is not None:
            self.lock = Lock()
            self.sfile = open(sentences_file, 'w')

    def blacklist_url(self, url: str, **kwargs):
        print(f'BLACKLISTING {url} (kwargs={kwargs})')
        self._blacklist.add(url)

    def save_url(self, url: str, parent: str = None):
        if url not in self._saved_urls:
            self._saved_urls.add(url)
            print("URL saved for later: %s (parent: %s)" % (url, parent))

    def is_url_blacklisted(self, url: str) -> bool:
        return url in self._blacklist

    def sentence_exists(self, sentence: str) -> bool:
        return sentence in self._sentences

    def save_page(self, page):
        self._pages[page.url] = page
        if page.new_sg and self.sfile is not None:
            with self.lock:
                self.sfile.write("\n".join((s.text for s in page.new_sg)))
        print("SAVING %s " % page)

    def get_page(self, url: str, **kwargs) -> Page:
        if url in self._pages:
            return self._pages[url]
        return Page(url=url, score=PageScore(), **kwargs)

    def close(self):
        if self.sfile:
            self.sfile.close()
            self.sfile = None

    def save_seed(self, seed: str):
        print("  * %s" % seed)
