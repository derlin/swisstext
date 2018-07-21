from typing import Optional, List

import yaml
import sys
import importlib
from os import path

from swisstext.config.base_config import BaseConfig
from swisstext.scraping.pipeline import Pipeline
import logging

from swisstext.searching.interfaces import ISaver
from swisstext.searching.pipeline import SearchEngine

logger = logging.getLogger(__name__)

# should be the same as the interface name (but camelcase => underscore)
# and in the order expected by the Pipeline's __init__ method.
_search_engine_entries = [
    'searcher',
    'saver'
]


class Config(BaseConfig):
    class Options:
        def __init__(self, max_results=10, force_x_new=0):
            self.max_results = max_results
            self.force_x_new = force_x_new

    def __init__(self, config_path=None):
        super().__init__(__file__, Config.Options, config_path)

    @property
    def valid_tool_entries(self) -> List[str]:
        return _search_engine_entries

    @property
    def interfaces_package(self) -> Optional[str]:
        return ISaver.__module__

    @property
    def tool_entry_name(self) -> str:
        return 'search_engine'

    def create_search_engine(self) -> SearchEngine:
        return SearchEngine(*self.get_tools())
