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


class ISplitter(ABC):

    @abstractmethod
    def split(self, text: str) -> List[str]:
        pass

    def split_all(self, texts: List[str]) -> List[str]:
        return [splitted for t in texts for splitted in self.split(t)]


class ISentenceFilter(ABC):

    @abstractmethod
    def is_valid(self, sentence):
        pass

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


class IPageSaver(ABC):

    @abstractmethod
    def sentence_exists(self, sentence: str):
        pass

    @abstractmethod
    def save_page(self, page) -> List[str]:
        pass

    @abstractmethod
    def get_page(self, url: str):
        pass