import importlib
import logging
from io import IOBase
from abc import ABC, abstractmethod
from typing import List, Optional, Union, Dict

import yaml


class BaseConfig(ABC):

    def __init__(self, default_config_path: str, option_class: classmethod = dict,
                 config: Union[str, dict, IOBase] = None):

        with open(default_config_path) as default_file:
            default_dict = yaml.safe_load(default_file)
        # load the user config, if given
        if config:
            config_dict = self._load_config_dict(config)
        # merge the two config, giving priority to the user config
        self.conf: Dict = self.merge_dicts(default_dict, config_dict)
        # instantiate the general options holder
        self.options = option_class(**self.conf['options'])
        # instantiate a logger
        self.logger = logging.getLogger(__name__)

    def _load_config_dict(self, config: Union[str, dict, IOBase]) -> Dict:
        """
        If config is a path or a file object, use yaml to read its content into a dict.
        If config is already a dict, just return it. Throw an error for any other case.
        """
        if isinstance(config, dict):
            return config
        elif type(config) is str:
            # a string is considered a path to a file
            with open(config) as config_file:
                return yaml.safe_load(config_file)
        elif isinstance(config, IOBase):
            return yaml.safe_load(config)
        else:
            raise ValueError(f"Trying to load a config from something else than a path, a file or a dict")

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
                raise RuntimeError(
                    "Error instantiating %s (%s.%s(%s))" %
                    (e, module_name, class_name, arguments)) from err

        return tools

    @staticmethod
    def _to_camelcase(text):
        """
        Converts underscore_delimited_text to camelCase.
        Useful for JSON output
        """
        return ''.join(word.title() for word in text.split('_'))

    @classmethod
    def _get_relative_path(cls, file, config_path='config.yaml'):
        from os import path
        return path.join(path.dirname(path.realpath(file)), config_path)

    @classmethod
    def merge_dicts(cls, default, overrides):
        import collections
        for k, v in overrides.items():
            if isinstance(v, collections.Mapping):
                default[k] = cls.merge_dicts(default.get(k, {}), v)
            else:
                default[k] = v
        return default
