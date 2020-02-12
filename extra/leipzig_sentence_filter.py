"""
This SentenceFilter more or less reproduces the behavior of older versions of the
`Leipzig Corpora Collection <https://wortschatz.uni-leipzig.de/en/download/>`_ crawler.

It is however less suited for the Swiss German case.
"""
import os
from swisstext.cmd.scraping.tools.pattern_sentence_filter import PatternSentenceFilter


class LeipzigSentenceFilter(PatternSentenceFilter):

    def __init__(self):
        super().__init__(os.path.realpath(__file__)[:-2] + 'yaml')