from io import IOBase
from typing import Optional, List, Union

from .interfaces import ISaver
from .pipeline import Pipeline
from ..base_config import BaseConfig

# should be the same as the interface name (but camelcase => underscore)
# and in the order expected by the Pipeline's __init__ method.
_pipeline_entries = [
    'crawler',
    'normalizer',
    'splitter',
    'sentence_filter',
    'sg_detector',
    'seed_creator',
    'url_filter',
    'decider',
    'saver']


class Config(BaseConfig):
    """
    The default configuration file for the scraping pipeline is defined in ``config.yaml``. This is the best way
    to understand what options are available.
    """

    class Options:
        """Holds the general options for the scraping pipeline."""

        def __init__(self, num_workers=1, min_proba=0.85, crawl_depth=2, **kwargs):
            # do some checks first
            if num_workers < 0:
                raise Exception('Wrong value for argument num_workers: should be > 0')
            if not 0 <= min_proba <= 1:
                raise Exception('Wrong value for argument min_proba: should be between 0 and 1')
            if crawl_depth < 0:
                raise Exception('Wrong value for argument crawl_depth: should be > 0')

            self.num_workers = num_workers  #: maximum number of threads to use
            self.min_proba = min_proba  #: minimum Swiss German probability to keep a sentence
            self.crawl_depth = crawl_depth  #: maximum depth of the crawl, inclusive.

    def __init__(self, config: Union[str, dict, IOBase] = None):
        super().__init__(self._get_relative_path(__file__), Config.Options, config)

    @property
    def valid_tool_entries(self) -> List[str]:
        return _pipeline_entries

    @property
    def interfaces_package(self) -> Optional[str]:
        return ISaver.__module__

    @property
    def tool_entry_name(self) -> str:
        return 'pipeline'

    def create_pipeline(self) -> Pipeline:
        """
        Instantiate a pipeline from the YAML configuration.
        """
        return Pipeline(*self.instantiate_tools(), min_proba=self.options.min_proba)
