import logging
from typing import Optional, List

from swisstext.config.base_config import BaseConfig
from swisstext.scraping.pipeline import Pipeline, ISaver

logger = logging.getLogger(__name__)

# should be the same as the interface name (but camelcase => underscore)
# and in the order expected by the Pipeline's __init__ method.
_pipeline_entries = [
    'crawler',
    'splitter',
    'sentence_filter',
    'sg_detector',
    'seed_creator',
    'decider',
    'saver']


class Config(BaseConfig):
    class Options:
        def __init__(self, num_workers=1, min_proba=0.85, crawl_depth=2):
            self.num_workers = num_workers
            self.min_proba = min_proba
            self.crawl_depth = crawl_depth

    def __init__(self, config_path=None):
        super().__init__(self._get_relative_path(__file__), Config.Options, config_path)

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
        return Pipeline(*self.instantiate_tools(), min_proba=self.options.min_proba)
