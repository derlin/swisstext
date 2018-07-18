import yaml
import sys
import importlib
from os import path
from swisstext.pipeline import Pipeline


class Config:
    class Options:
        def __init__(self,
                     num_workers=1,
                     min_proba=0.85,
                     crawl_depth=2,
                     mongo=None):
            self.num_workers = num_workers
            self.min_proba = min_proba
            self.crawl_depth = crawl_depth
            self.mongo = dict(host='localhost', port=27017, db='tmp')
            if mongo:
                self.mongo.update(mongo)

    def __init__(self, config_path=None):
        if config_path is None:
            config_path = path.join(path.dirname(path.realpath(__file__)), 'config.yaml')

        self.conf = yaml.safe_load(open(config_path))
        self.options = Config.Options(**self.conf['options'])

    def create_pipeline(self) -> Pipeline:
        entries = ['crawler', 'splitter', 'filter', 'detector', 'seed_creator', 'decider', 'saver']
        tools = []

        for e in entries:
            if e not in self.conf['pipeline']:
                print("Error: missing configuration pipeline.%s" % e)
                sys.exit(1)

            try:
                module_name, class_name = self.conf['pipeline'][e].rsplit(".", 1)
                ToolClass = getattr(importlib.import_module(module_name), class_name)
                tools.append(ToolClass())
            except Exception as err:
                print("Error instantiating %s: %s" % (e, err))
                sys.exit(1)

        return Pipeline(*tools, min_proba=self.options.min_proba)
