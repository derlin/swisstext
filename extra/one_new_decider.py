from swisstext.cmd.scraping.data import Page
from swisstext.cmd.scraping.tools import BasicDecider


class OneNewDecider(BasicDecider):

    def should_children_be_crawled(self, page: Page) -> bool:
        if super().should_children_be_crawled(page):
            # if parent_url is None it means the url comes from
            # either a file or a seed, thus it might be interesting to
            # go further anyway. But in case we already have a crawl depth > 1,
            # just don't try going further if no new sg is found
            return page.parent_url is None or len(page.new_sg) > 0
