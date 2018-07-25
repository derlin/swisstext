from datetime import datetime, timedelta

from pytimeparse.timeparse import timeparse

from swisstext.scraping.interfaces import IDecider
from swisstext.scraping.data import Page

MIN_RECRAWL_DELTA = "7d"
MIN_RATIO = 0


class BasicDecider(IDecider):

    def __init__(self, min_ratio=MIN_RATIO, min_recrawl_delta: str = None, **kwargs):
        self.min_ratio = min_ratio
        try:
            delta_sec = timeparse(min_recrawl_delta)
        except:
            delta_sec = timeparse(MIN_RECRAWL_DELTA)
        self.min_recrawl_delta = timedelta(seconds=delta_sec)

    def should_page_be_crawled(self, page: Page) -> bool:
        return page.is_new() or \
               page.score.delta_count > 0 or \
               datetime.utcnow() - page.score.delta_date > self.min_recrawl_delta

    def should_children_be_crawled(self, page: Page) -> bool:
        # TODO: use new_count vs sg_count ?
        return page.sg_count > 0 and page.sentence_count / page.sg_count > self.min_ratio

    def should_url_be_blacklisted(self, page: Page) -> bool:
        return page.is_new() and page.sg_count == 0


class OnlyNewDecider(BasicDecider):

    def should_page_be_crawled(self, page: Page) -> bool:
        return page.is_new()
