import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

import yaml
import sys
import importlib
from os import path


class BaseConfig(ABC):

    def __init__(self, child_file, option_class: classmethod = dict, config_path=None):
        if config_path is None:
            config_path = path.join(path.dirname(path.realpath(child_file)), 'config.yaml')

        self.conf = yaml.safe_load(open(config_path))
        self.options = option_class(**self.conf['options'])
        self.logger = logging.getLogger(__name__)

    @property
    @abstractmethod
    def valid_tool_entries(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def interfaces_package(self) -> Optional[str]:
        return None

    @property
    @abstractmethod
    def tool_entry_name(self) -> str:
        pass

    def get(self, prop_name, default=None):
        if '.' in prop_name:
            root = self.conf
            props = prop_name.split('.')
            for key in props:
                if root:
                    root = root.get(key, None)
            return default if root is None else root
        else:
            return self.conf.get(prop_name, default)

    def instantiate_tools(self) -> List[object]:
        tools = []
        root = self.conf[self.tool_entry_name]
        base_package = root.get('_base_package', '')

        for e in self.valid_tool_entries:
            if e not in root:
                self.logger.warning("missing entry in toolchain '%s'" % e)
                module_name = self.interfaces_package
                class_name = "I%s" % self._to_camelcase(e)
            else:
                qualified_name = root[e]
                if base_package and qualified_name.startswith("."):
                    qualified_name = base_package + qualified_name
                module_name, class_name = qualified_name.rsplit(".", 1)

            arguments = self.conf.get("%s_options" % e) or {}

            try:
                ToolClass = getattr(importlib.import_module(module_name), class_name)
                tools.append(ToolClass(**arguments))
            except Exception as err:
                self.logger.exception("Error instantiating %s (%s.%s(%s))" %
                                      (e, module_name, class_name, arguments))
                sys.exit(1)

        return tools

    @staticmethod
    def _to_camelcase(text):
        """
        Converts underscore_delimited_text to camelCase.
        Useful for JSON output
        """
        return ''.join(word.title() for word in text.split('_'))
