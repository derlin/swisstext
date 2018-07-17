from multiprocessing import Lock

from swisstext.interfaces import IPageSaver
from swisstext.common.data import Page, PageScore
import logging

logger = logging.getLogger(__name__)


class ConsoleSaver(IPageSaver):

    def __init__(self, sentences_file: str = None):
        self._blacklist = set()
        self._sentences = set()
        self.sfile = None

        if sentences_file is not None:
            self.lock = Lock()
            self.sfile = open(sentences_file, 'w')

    def blacklist_url(self, url: str):
        print("BLACKLISTING %s" % url)
        self._blacklist.add(url)

    def is_url_blacklisted(self, url: str) -> bool:
        return url in self._blacklist

    def sentence_exists(self, sentence: str) -> bool:
        return sentence in self._sentences

    def save_page(self, page):
        if page.new_sg and self.sfile is not None:
            with self.lock:
                self.sfile.write("\n".join(page.new_sg))
        print("SAVING %s (sg=%d/%d)" % (page, page.sg_count, page.sentence_count))

    def get_page(self, url: str, **kwargs):
        return Page(url=url, score=PageScore(), **kwargs)

    def close(self):
        if self.sfile:
            self.sfile.close()
            self.sfile = None
