"""
This module defines interfaces for each tool or decision maker used in the scraping process.
This makes it easy to test new ways or to tune one aspect of the scraper while keeping most of the code unchanged.

See the :py:mod:`swisstext.cmd.scraping.tools` module for implementations.
"""

from abc import abstractmethod, ABC
from typing import List

from .data import Page


class ICrawler(ABC):
    """
    [ABSTRACT] This tool is in charge of crawling a page. More specifically, it should be able to:
    1. extract the text of the page (stripped of any HTML or other structural clue),
    2. extract links pointing to other pages
    """

    class CrawlError(Exception):
        """This wrapper should be used for any exception that arise during scraping."""

        def __init__(self, message: str):
            super().__init__(message)

    class CrawlResults:
        """Holds the results of a page crawl."""

        def __init__(self, text: str, links: List[str]):
            self.text: str = text
            """the clean text found in the page, free of any structural marker such as HTML tags, etc."""
            self.links: List[str] = links
            """A list of interesting links found in the page. By interesting, we mean:
            * no duplicates
            * different from the current page URL (no anchors !)
            * if possible, no link pointing to unparseable resources (zip files, images, etc.)
            The method :py:meth:`swisstext.cmd.scraping.link_utils.filter_links` is available to do the filtering. 
            """

    @abstractmethod
    def crawl(self, url: str) -> CrawlResults:
        """[ABSTRACT]
        Should crawl the page and extract the text and the links into a :py:class:`ICrawler.CrawlResults` instance."""
        pass


class ISplitter:
    """
    A splitter should take a [long] text (extracted from a web page) and split it into well-formed sentences.
    The default implementation just splits on the newline character.
    """

    def split(self, text: str) -> List[str]:
        """This should be overriden. The default implementation just splits on newlines."""
        return text.splitlines()

    def split_all(self, texts: List[str]) -> List[str]:
        """Takes a list of texts and returns a list of sentences (see :py:meth:`split`)."""
        return [splitted for t in texts for splitted in self.split(t)]


class ISentenceFilter:
    """
    A sentence filter should be able to tell if a given sentence is well-formed (i.e. valid) or not.
    """

    def is_valid(self, sentence: str) -> bool:
        """This should be overriden. The default implementation just returns true."""
        return True

    def filter(self, sentences: List[str]) -> List[str]:
        """Filter a list of sentences by calling :py:meth:`ISentenceFilter.is_valid` on each element."""
        return [s for s in sentences if self.is_valid(s)]


class ISgDetector(ABC):
    """
    [ABSTRACT] An SG Detector is a Language Identifier supporting Swiss German.
    """

    @abstractmethod
    def predict(self, sentences: List[str]) -> List[float]:
        """
        [ABSTRACT] Predict the Swiss German probability (between 0 and 1) of a list of sentences.
        """
        pass

    def predict_one(self, sentence: str) -> float:
        """
        Call :py:meth:`predict` with one sentence.
        """
        return self.predict([sentence])[0]


class ISeedCreator(ABC):
    """
    [ABSTRACT] A seed creator should generate seeds, i.e. search queries, out of Swiss German sentences.
    """

    @abstractmethod
    def generate_seeds(self, sentences: List[str], max=10, stopwords: List[str] = list()) -> List[str]:
        """
        [ABSTRACT] Should generate interesting seeds.

        :param sentences: the sentences
        :param max: maximum number of seeds to return
        :param stopwords: an optional list of words to exclude from generated seeds
        :return: a list of seeds
        """
        # TODO use a generator instead of a list as return type ?
        pass


class IDecider:
    """
    A decider should implement the logic behind whether or not a URL is considered interesting/should be crawled.
    """

    def should_url_be_blacklisted(self, page: Page) -> bool:
        """
        Decide if a URL/page is blacklisted. The default implementation returns true if the URL has never been
        visited before *and* contains no Swiss German sentence. The *new* criteria is important to avoid blacklisting
        a page that changed over time, but contained once interesting sentences (and thus might be referenced in
        the persistence layer).
        """
        return page.is_new() and page.sg_count == 0

    def should_page_be_crawled(self, page: Page) -> bool:
        """
        Decide if a page should be scraped on this run. By default, it returns always true, but we could devise other
        rules based on the last crawl, etc.
        """
        return True

    def should_children_be_crawled(self, page: Page) -> bool:
        """
        Decide if the links found on a page should be scraped on this run. Returns true by default.

        .. note:
            This decision is more important in case of a new page (one that has never been visited before),
            as children might never have another chance to be discovered.
        """
        return True


class ISaver(ABC):
    """
    [ABSTRACT] The saver is responsible for persisting everything somewhere, such as a database, a file or the console.
    """

    def __init__(self, **kwargs):
        """

        .. warning:
            Currently, it is mandatory to declare a ``**kwargs`` argument in the constructor for all subclasses,
            because the default configuration (see :py:class:`swisstext.cmd.scraping.Config`) of the system passes
             ``host``, ``port`` and ``db`` arguments automatically to the saver.

            This is because some entrypoints need to fetch informations from Mongo and thus rely on
            those options to connect. This is not yet part of an interface... but should be !
        """
        pass

    @abstractmethod
    def blacklist_url(self, url: str):
        """
        [ABSTRACT] Add the `url` to a blacklist.

        .. todo:
            Pass the page object instead of just the URL ?
        """
        pass

    @abstractmethod
    def is_url_blacklisted(self, url: str) -> bool:
        """
        [ABSTRACT] Tells if the given `url` is part of the blacklist. This is called at the beginning,
        to avoid scraping pages unnecessarily.
        """
        pass

    @abstractmethod
    def sentence_exists(self, sentence: str) -> bool:
        """
        [ABSTRACT] Tells if the given Swiss German `sentence` already exists.
        Only new sentences will be added to the page's :py:attr:`~swisstext.cmd.scraping.data.Page.new_sg` attribute.
        """
        pass

    @abstractmethod
    def save_page(self, page: Page):
        """
        [ABSTRACT] Persist a page.
        This is called after the scraping, so all page's attributes are set, including the
        list of new :py:class::`~swisstext.cmd.scraping.data.Sentence` found.
        """
        pass

    def get_page(self, url: str, **kwargs):
        """
        Load a page. The simplest implementation is just ``return Page(url)``.
        If the subclass uses a data store, it should also populate the other page attributes (e.g. the score
        information) so that the :py:class::`IDecider` can make clever decisions.
        """
        pass

    @abstractmethod
    def save_seed(self, seed: str):
        """
        [ABSTRACT] Persist a seed (usually generated by the :py:class::`ISeedGenerator`).
        """
        pass

    def save_seeds(self, seeds: List[str]):
        """Persist multiple seeds (see :py:meth:`save_seed`)."""
        for seed in seeds:
            self.save_seed(seed)
