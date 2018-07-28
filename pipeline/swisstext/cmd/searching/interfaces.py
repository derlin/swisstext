from abc import ABC, abstractmethod
from typing import Iterable, List

from .data import Seed
import itertools


class ISearcher(ABC):

    @abstractmethod
    def search(self, query) -> Iterable[str]:
        pass

    def top_results(self, query, max_results=10) -> List:
        return list(itertools.islice(self.search(query), max_results))


class ISaver(ABC):

    @abstractmethod
    def save_seed(self, seed: Seed):
        pass

    def link_exists(self, url: str) -> bool:
        return False
