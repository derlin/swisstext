"""
This module defines the generic data structures used across the module / between the different tools.
They have been thought to be decoupled from MongoDB for better flexibility/adaptability.
"""

from typing import List


class PageScore:
    """
    Scoring information for a page used, among other things, to decide if a URL should be crawled or not.
    """

    def __init__(self, count=0, delta_count=0, delta_date=None):
        self.count = count  #: total number of new sentences found on this page (for all the visits)
        self.delta_count = delta_count  #: number of new sentences found on this page in the last visit
        self.delta_date = delta_date  #: date of the last visit (in UTC) or None if never visited


class Sentence:
    """
    Information about a sentence.
    """

    def __init__(self, text: str, proba: float):
        self.text = text  #: the exact text
        self.proba = proba  #: the Swiss German probability

    def __str__(self):
        return "(<%.2f|%s>)" % (self.proba * 100, self.text)


class Page:
    """
    Information about a page.
    Some attributes should be defined upon creation (see :py:meth:`swisstext.cmd.scraping.interfaces.ISaver.get_page`),
    will other will be added/used incrementally by the different tools of the pipeline.
    """

    def __init__(self, url, score=None, parent_url=None):
        self.url = url  #: the URL of the page
        self.parent_url = parent_url  #: the parent URL, if the crawl depth is > 1
        self.blacklisted = False  #: is the URL blacklisted ?
        self.crawl_results = None  #: results of the crawl (see :py:class:`~cmd.scraping.interfaces.ICrawler`)
        self.new_sg: List[Sentence] = []  #: new sentences found
        self.sentence_count = 0  #: total number of sentences on the page
        self.sg_count = 0  #: number of Swiss German sentences on the page, wether they are new or not
        self.score: PageScore = score or PageScore()  #: page score

    def is_new(self) -> bool:
        """Test if the page is new or not, based on the :py:attr:`delta_date`."""
        return not self.score.delta_date

    def __str__(self):
        return "(<Page %s, sg=%d/%d>)" % (self.url, self.sg_count, self.sentence_count)
