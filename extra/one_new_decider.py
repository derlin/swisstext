from swisstext.cmd.scraping.data import Page
from swisstext.cmd.scraping.tools import BasicDecider


class OneNewDecider(BasicDecider):

    def should_children_be_crawled(self, page: Page) -> bool:
        if super().should_children_be_crawled(page):
            # just don't try going further if no new sg is found
            return len(page.new_sg) > 0
