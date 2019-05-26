"""
This module encapsulates all the configuration needed to run a multi-steps toolchain.
It is used by both commandline tools.

Config objects can easily be populated from a YAML configuration file. This file should have the following structure:

.. code-block:: yaml

    # This entry defines general options that will be stored in :py:attr:`BaseConfig.options`.
    options:
      key1: value1

    # This entry defines tools to instantiate
    # the actual name is specified in the subclass by overriding :py:attr:`BaseConfig.tool_entry_name`
    # valid interface names are specified in the sublcass by overriding :py:attr:`valid_tool_entries`
    tool_entry_name:
        # optional default package for relative entries
        _base_package: some.default.module
        # list of tools
        interface_name_1: absolute.module.ToolClassName1
        interface_name_2: .ToolClassName2 # will be expanded to some.default.module.ToolClassName2

    # any entry in the form [interface_name]_options defines options that will be passed to the
    # tool class upon construction. Here, for example, the actual instantiation will be:
    #    absolute.module.ToolClassName1(param_1=some_value, param_X=some_other_value)
    interface_name_1_options:
        param_1: some_value
        param_X: some_other_value

.. seealso:

    Modules :py:mod:`swisstext.cmd.searching.config` and :py:mod:`swisstext.cmd.scraping.config`
        For examples of subclasses and usages.
"""

import importlib
import logging
from io import IOBase
from abc import ABC, abstractmethod
from typing import List, Optional, Union, Dict

import yaml


class BaseConfig(ABC):
    """
    This class encapsulates the configuration options of a toolchain. It is able to load options from YAML files
    and also to instantiate tools from a dictionary of module+class names.
    """

    def __init__(self, default_config_path: str, option_class: classmethod = dict,
                 config: Union[str, dict, IOBase] = None):
        """
        Create a configuration.

        Subclasses should provide the path to a default configuration (YAML file) and optionally an
        option class to hold general options. The config is provided by the user and can be a file, a path
        to a file or even a dictionary (as long as it has the correct structure).

        :param default_config_path: the absolute path to a default configuration file.
        :param option_class: the class to use for holding global options (a dictionary by default).
        :param config: user configuration that overrides the default options. config can be either a path or a
            file object of a YAML configuration, or a dictionary
        :raises ValueError: if config is not of a supported type
        """
        default_dict, config_dict = {}, {}
        # load the default config first
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
        """
        Should return the list of valid tool entries under the :py:attr:`tool_entry_name`.
        Note that the order of tools in the list defines the order of tools instances returned by
        :py:meth:`instantiate_tools`.
        """
        pass

    @property
    @abstractmethod
    def interfaces_package(self) -> Optional[str]:
        """
       Should return the complete package where the interfaces are defined, if any.
       In case this is defined and a tool is missing from the list, we will try to instantiate
       the interface instead.
       """
        return None

    @property
    @abstractmethod
    def tool_entry_name(self) -> str:
        """
        Should return the name of the tool_entries option, i.e. the YAML path to the dictionary of
        [interface name, canonical class to instantiate].
        """
        pass

    def get(self, prop_name, default=None):
        """
        Get a value from the YAML configuration file. This method supports paths with ".", for example:

        * `options`: returns the top-level "options"
        * `tool_entry.tool_name`: return the value of tool_name under tool_entry

        :param prop_name: the path of the property to retrieve
        :param default: the default value if the property is not found
        :return: the property value or `default`
        """
        root, prop = self._get_subdict(prop_name)
        return default if root is None else root.get(prop, default)

    def set(self, prop_name, value):
        """
        Set a value using the property dot syntax. See :py:meth:`get` to see how it works.
        """
        root, prop = self._get_subdict(prop_name)
        if root and prop in root:
            root[prop] = value

    def dumps(self):
        return yaml.dump(self.conf)

    def _get_subdict(self, prop_name):
        root = self.conf
        props = prop_name.split('.')

        if '.' in prop_name:
            for key in props[:-1]:
                root = root.get(key, None)
                if root is None:
                    break

        return root, props[-1]

    def instantiate_tools(self) -> List[object]:
        """
        For each :py:attr:`valid_tool_entries` under :py:attr:`tool_entry_name`, try to create an instance.
        In case a tool is not defined and :py:attr:`interfaces_package` is not None,
        it will try to instantiate the tool name interface instead.

        :return: a list of tool instances, in the same order as :py:attr:`interfaces_package`
        :raises RuntimeError: if a tool could not be instantiated
        """
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
        Converts underscore_delimited_text to CamelCase.
        Example: "tool_name" becomes "ToolName"
        """
        return ''.join(word.title() for word in text.split('_'))

    @classmethod
    def _get_relative_path(cls, file, config_path='config.yaml'):
        """
        :param file: the working directory / context
        :param config_path: the relative path to a file
        :return: the absolute file after expansion
        """
        from os import path
        return path.join(path.dirname(path.realpath(file)), config_path)

    @classmethod
    def merge_dicts(cls, default, overrides):
        """
        Merge ``override`` into ``default`` recursively.
        As the names suggest, if an entry is defined in both, the value in ``overrides`` takes precedence.
        """
        import collections
        for k, v in overrides.items():
            if isinstance(v, collections.Mapping):
                default[k] = cls.merge_dicts(default.get(k, {}), v)
            else:
                default[k] = v
        return default
