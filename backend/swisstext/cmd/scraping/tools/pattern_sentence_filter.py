"""
This module contains an implementation of :py:class:`~swisstext.cmd.scraping.interfaces.ISentenceFilter` that uses
simple rules to filter "well-formed" sentences.

How it works
------------
Each sentence is checked against a list of rules and rejected / considered invalid if any of those rules fail.
Rules are thus *AND-based*.

Rules are defined using a simple YAML syntax and can be of two types: *length-based* (character count)
 or *pattern-based* (regular expressions). They are checked in the same order they are defined.

.. note::

    * Regular expressions can be quite expensive, so try to limit their complexity to the minimum required.
    * Rules are checked in the same order as they are defined, so it is advised to put the most generic / efficient
      ones first.

.. note::

    This module uses the `regex library <https://pypi.org/project/regex/>`_ (version V0)
    instead of the default re. You can thus freely use
    `unicode regular expressions <https://www.regular-expressions.info/unicode.html>`_
    in your rules.

Rule syntax
-----------

**Length-based rules (length)** must specify *at least one* of *min* or *max* length,
i.e. the bounds on the number of characters.
The rule succeeds if ``min <= len(s) <= max``. Here is an example:

.. code-block:: yaml

    - max_length:
      descr: too long
      length:
        max: 1000

**Pattern-based rules (find)** a bit similarly, but instead of counting the number of characters, they count the number
of occurrences of a *pattern* (i.e. the number of matches when calling ``re.findall(pattern, s)``).
The rule itself can be based on the raw count or based on a ratio:

* count: the rule succeeds if ``min <= nb_matches <= max`` (inclusive !)
* ratio: the rule succeeds if ``min <= len(s) / (len(s) - nb_matches + 1) <= max```

Here are examples:

.. code-block:: yaml

    - min_words:
      descr: not enough words
      find:
        pattern: '\S+'
        count:
          min: 5

    - letters_proportional:
      descr: not enough letters proportion
      find:
        pattern: '[\W|\d]'
        ratio:
          max: 1.4

Finally, **an if condition** can be used. If conditions are checked first, and if the check fails, the rule is
simply ignored:

.. code-block:: yaml

    - ellipsis:
      descr: ellispsis on short sentences.
      if:
        length:
          max: 30
      find:
        pattern: '(\.\s?){3}$'
        count:
          max: 0

Rules can additionnally specify examples that could be used to check quickly if they work. For example:

.. code-block:: yaml

    - spelled_words:
      descr: W O R D
      find:
        pattern: ' ([\p{L}] ){3,}'
        count:
          max: 0
      examples:
        - 'you must B E L I E V E me.'
        - 'span spells S P A N.'
        - 'S P A N means span!!'
"""

import regex
import yaml
import logging
from os import path

from swisstext.cmd.scraping.interfaces import ISentenceFilter

logger = logging.getLogger(__name__)


class PatternSentenceFilter(ISentenceFilter):
    """
    By default, rules are loaded from the default file ``pattern_sentence_filter.yaml`` in the current directory.
    You can override this by passing a path to the constructor (``rulespath`` argument).
    """

    def __init__(self, rulespath=None):
        """Load rules from the default YAML file or the path provided."""
        if rulespath is None:
            rulespath = path.join(path.dirname(path.realpath(__file__)), 'pattern_sentence_filter.yaml')

        self.rulespath = rulespath
        self.rules = Rules(yaml.safe_load(open(rulespath)))

    def is_valid(self, sentence):
        """Returns true only if all the rules were respected."""
        return not self.rules.is_invalid(sentence)


class MinMax:
    """Encapsulates and handles min/max bounds. A bound set to -1 will be ignored."""

    def __init__(self, min=-1, max=-1):
        self.min = min
        self.max = max

    def is_invalid(self, s) -> bool:
        return self.is_out_of_range(len(s))

    def is_out_of_range(self, n) -> bool:
        return (self.min >= 0 and self.min > n) or (self.max >= 0 and self.max < n)

    def __repr__(self):
        return "(min={}, max={})".format(self.min, self.max)


class Find:
    """Handles pattern-based rule logic (find entry in yaml)"""

    def __init__(self, pattern, count=None, ratio=None):
        if count is None and ratio is None:
            logger.warning(f"{pattern}: missing find condition: count or ratio...")
        self.pattern = regex.compile(pattern)
        self.count = MinMax(**count) if count else None
        self.ratio = MinMax(**ratio) if ratio else None

    def is_invalid(self, s):
        matches = self.pattern.findall(s)
        nb_matches = len(matches)
        if self.count and self.count.is_out_of_range(nb_matches):
            return True
        if self.ratio:
            s_len = len(s)
            ratio = s_len / (s_len - nb_matches + 1)
            return self.ratio.is_out_of_range(ratio)
        return False

    def __repr__(self):
        return "(pattern=%s, count=%s, ratio=%s)" % (self.pattern, self.count, self.ratio)


class Rule:
    """Encapsulates one rule"""

    def __init__(self, id, descr, find=None, length=None, examples=None, **kwargs):
        self.id = id
        self.descr = descr
        self.examples = examples
        self.iff = []
        # TODO: better way ?
        if 'if' in kwargs:  # if is a reserved keyword in python
            if 'length' in kwargs['if']:
                self.iff.append(MinMax(**kwargs['if']['length']))
            if 'pattern' in kwargs['if']:
                self.iff.append(Find(**kwargs['if']['pattern']))

        self.find = Find(**find) if find else None
        self.length = MinMax(**length) if length else None

    def is_applicable(self, s) -> bool:
        """Check for the if condition"""
        return not any([iff.is_invalid(s) for iff in self.iff])

    def is_invalid(self, s) -> bool:
        if self.is_applicable(s):
            if (self.length and self.length.is_invalid(s)) or (self.find and self.find.is_invalid(s)):
                logger.debug("%s FAILED on |%s|" % (self, s))
                return True
            return False
        else:
            # logger.debug("SKIPPED   RULE %s: |%s|" % (self.descr, s))
            return False

    def __str__(self):
        return "RULE %d %s" % (self.id, self.descr)

    def __repr__(self):
        return "{}: [if {}] find={}, length={}".format(self.descr, self.iff, self.find, self.length)


class Rules:
    """
    This class represents a list of rules.
    """

    def __init__(self, rules_dict):
        """
        :param rules_dict: a dictionary of rules (as loaded by yaml)
        """
        self.rules = [Rule(idx + 1, **r) for (idx, r) in enumerate(rules_dict)]  # [:1]

    def is_invalid(self, sentence: str) -> bool:
        """Returns true if any rule that apply failed."""
        for idx, r in enumerate(self.rules):
            if r.is_invalid(sentence):
                # print("RULE %d %s FAILED on |%s|" % (idx, r.descr, sentence))
                return True
        return False

    def print_rules(self):
        """Prints all the rules, useful for debug."""
        for idx, r in enumerate(self.rules):
            print(idx, "=>", r.__repr__())

    def __getitem__(self, idx):
        return self.rules[idx]

    def __len__(self):
        return len(self.rules)


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=argparse.FileType('r'), default='-')
    parser.add_argument('-o', '--out', type=argparse.FileType('w'), default='-')
    parser.add_argument('-r', '--rules-file', default=None)

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)s: %(msg)s')

    psf = PatternSentenceFilter(rulespath=args.rules_file)

    args.out.write('\n'.join(
        t for t in args.input if psf.is_valid(t)
    ))
