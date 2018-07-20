import yaml
import sys
import importlib
from os import path
from swisstext.scraping.pipeline import Pipeline
import logging

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
    'page_saver']


class Config:
    class Options:
        def __init__(self, num_workers=1, min_proba=0.85, crawl_depth=2):
            self.num_workers = num_workers
            self.min_proba = min_proba
            self.crawl_depth = crawl_depth

    def __init__(self, config_path=None):
        if config_path is None:
            config_path = path.join(path.dirname(path.realpath(__file__)), 'config.yaml')

        self.conf = yaml.safe_load(open(config_path))
        self.options = Config.Options(**self.conf['options'])

    def create_pipeline(self) -> Pipeline:
        tools = []
        base_package = self.conf['pipeline'].get('_base_package', '')

        for e in _pipeline_entries:
            if e not in self.conf['pipeline']:
                logger.warning("missing configuration entry 'pipeline.%s'" % e)
                module_name = "swisstext.interfaces"
                class_name = "I%s" % self.to_camelcase(e)
            else:
                qualified_name = self.conf['pipeline'][e]
                if base_package and qualified_name.startswith("."):
                    qualified_name = base_package + qualified_name
                module_name, class_name = qualified_name.rsplit(".", 1)

            arguments = self.conf.get("%s_options" % e) or {}

            try:
                ToolClass = getattr(importlib.import_module(module_name), class_name)
                tools.append(ToolClass(**arguments))
            except Exception as err:
                logger.exception("Error instantiating %s (%s.%s(%s))" %
                                 (e, module_name, class_name, arguments))
                sys.exit(1)

        return Pipeline(*tools, min_proba=self.options.min_proba)

    @staticmethod
    def to_camelcase(text):
        """
        Converts underscore_delimited_text to camelCase.
        Useful for JSON output
        """
        return ''.join(word.title() for word in text.split('_'))
