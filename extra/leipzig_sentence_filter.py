import os
from swisstext.cmd.scraping.tools.pattern_sentence_filter import PatternSentenceFilter


class LeipzigSentenceFilter(PatternSentenceFilter):

    def __init__(self):
        super().__init__(os.path.realpath(__file__)[:-2] + 'yaml')