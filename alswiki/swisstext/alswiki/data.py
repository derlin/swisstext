import json

from swisstext.cmd.scraping.data import Page
from swisstext.cmd.scraping.interfaces import ICrawler
from swisstext.cmd.scraping.pipeline import PipelineWorker


class Article:
    def __init__(self, line):
        d = json.loads(line)
        self.title = d['title']
        self.section_titles = d['section_titles']
        self.section_texts = d['section_texts']

    @property
    def url(self):
        slug = self.title.replace(' ', '_')
        return 'https://als.wikipedia.org/wiki/' + slug

    @property
    def text(self):
        return '\n'.join(self.section_texts)


class PipelineWorkerWrapper(PipelineWorker):

    def _crawl_page(self, crawler: ICrawler, page: Page):
        assert hasattr(page, 'article')
        return ICrawler.CrawlResults(page.article.text, [])
