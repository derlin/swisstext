import logging
from io import IOBase
from typing import Optional, List, Union

from ..base_config import BaseConfig
from .interfaces import ISaver
from .pipeline import SearchEngine

logger = logging.getLogger(__name__)

# should be the same as the interface name (but camelcase => underscore)
# and in the order expected by the Pipeline's __init__ method.
_search_engine_entries = [
    'query_builder',
    'searcher',
    'saver'
]


class Config(BaseConfig):
    """
    The default configuration file for the searching pipeline (search engine) is defined in ``config.yaml``.
    This is the best way to understand what options are available.
    """

    class Options:
        def __init__(self, max_fetches=-1, max_results=10, **kwargs):
            # do some checks first
            if max_fetches != -1 and max_fetches < 1:
                raise Exception('Wrong value for argument max_fetches: should be -1 or > 0')
            if max_results <= 0 or (max_fetches != -1 and max_results > max_fetches):
                raise Exception('Wrong value for argument max_results: should be > 0 and <= max_fetches')

            self.max_fetches = max_fetches
            """
            Max number of URLs retrieved in one search (-1 for no limit).
            Note that this is only the number of URLs returned by the search engine, not the number of
            URLs added to the db. Indeed, duplicates or uninteresting URLs won't be saved (see max_results).
            """

            self.max_results = max_results
            """
            Max number of URLs saved from one search.
            Note that it should always be <= max_fetches. 
            """

    def __init__(self, config: Union[str, dict, IOBase] = None):
        super().__init__(self._get_relative_path(__file__), Config.Options, config)

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
        """
        Instantiate a search engine from the YAML configuration.
        """
        return SearchEngine(*self.instantiate_tools())
