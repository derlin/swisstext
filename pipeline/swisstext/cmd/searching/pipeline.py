from typing import List

from .data import Seed
from .interfaces import ISearcher, ISaver


class SearchEngine:
    def __init__(self, searcher: ISearcher, saver: ISaver):
        self.searcher = searcher
        self.saver = saver
        self.new_urls = set()

    def process(self, seeds: List[Seed], max_results=10):
        for seed in seeds:
            for link in self.searcher.top_results(seed.query, max_results):
                if link not in self.new_urls:
                    if not self.saver.link_exists(link):
                        seed.new_links.append(link)
                    self.new_urls.add(link)
            self.saver.save_seed(seed)
