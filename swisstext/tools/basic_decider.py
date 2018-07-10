from datetime import datetime, timedelta

from swisstext.interfaces import IDecider
from swisstext.page import Page

MIN_RECRAWL_DELTA = timedelta(days=7)
MIN_RATIO = 0


class BasicDecider(IDecider):

    def should_page_be_crawled(self, page: Page) -> bool:
        return page.is_new() or \
               page.score.delta_count > 0 or \
               datetime.utcnow() - page.score.delta_date > MIN_RECRAWL_DELTA

    def should_children_be_crawled(self, page: Page) -> bool:
        # TODO: use new_count vs sg_count ?
        return page.sg_count > 0 and page.sentence_count / page.sg_count > MIN_RATIO

    def should_url_be_blacklisted(self, page: Page) -> bool:
        return page.is_new() and page.sg_count == 0
