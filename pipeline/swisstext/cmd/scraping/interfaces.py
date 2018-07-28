from abc import abstractmethod, ABC
from typing import List


class ICrawler(ABC):
    class CrawlError(Exception):
        def __init__(self, message: str):
            super().__init__(message)

    class CrawlResults:
        def __init__(self, text: str, links: List[str]):
            self.text = text
            self.links = links

    @abstractmethod
    def crawl(self, url: str) -> CrawlResults:
        pass


class ISplitter:

    def split(self, text: str) -> List[str]:
        return text.split("\n")

    def split_all(self, texts: List[str]) -> List[str]:
        return [splitted for t in texts for splitted in self.split(t)]


class ISentenceFilter:

    def is_valid(self, sentence):
        return True

    def filter(self, sentences: List[str]) -> List[str]:
        return [s for s in sentences if self.is_valid(s)]


class ISgDetector(ABC):

    @abstractmethod
    def predict(self, sentences: List[str]) -> List[float]:
        pass

    def predict_one(self, sentence: str) -> float:
        return self.predict([sentence])[0]


class ISeedCreator(ABC):

    @abstractmethod
    def generate_seeds(self, sentences: List[str], max=10, stopwords: List[str] = list()) -> List[str]:
        pass


class IDecider:

    def should_url_be_blacklisted(self, page) -> bool:
        return page.is_new() and page.sg_count == 0

    def should_page_be_crawled(self, page) -> bool:
        return True

    def should_children_be_crawled(self, page) -> bool:
        return True


class ISaver(ABC):

    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def blacklist_url(self, url: str):
        pass

    @abstractmethod
    def is_url_blacklisted(self, url: str) -> bool:
        pass

    @abstractmethod
    def sentence_exists(self, sentence: str) -> bool:
        pass

    @abstractmethod
    def save_page(self, page):
        pass

    @abstractmethod
    def get_page(self, url: str, **kwargs):
        pass

    @abstractmethod
    def save_seed(self, seed: str):
        pass

    def save_seeds(self, seeds: List[str]):
        for seed in seeds:
            self.save_seed(seed)