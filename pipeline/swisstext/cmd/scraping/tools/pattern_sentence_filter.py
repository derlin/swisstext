import re
import yaml
import logging
from os import path

from ..interfaces import ISentenceFilter

logger = logging.getLogger(__name__)


class PatternSentenceFilter(ISentenceFilter):
    def __init__(self, rulespath=None):
        if rulespath is None:
            rulespath = path.join(path.dirname(path.realpath(__file__)), 'pattern_sentence_filter.yaml')

        self.rules = Rules(yaml.safe_load(open(rulespath)))

    def is_valid(self, sentence):
        return not self.rules.is_invalid(sentence)


class MinMax:
    def __init__(self, min=-1, max=-1):
        self.min = min
        self.max = max

    def is_invalid(self, s):
        return self.is_out_of_range(len(s))

    def is_out_of_range(self, n):
        return (self.min >= 0 and self.min > n) or (self.max >= 0 and self.max < n)

    def __repr__(self):
        return "(min={}, max={})".format(self.min, self.max)


class Find:
    def __init__(self, pattern, count=None, ratio=None):
        if count is None and ratio is None:
            logger.warning("%s: missing find condition: count or ratio..." % self)
        self.pattern = pattern
        self.count = MinMax(**count) if count else None
        self.ratio = MinMax(**ratio) if ratio else None

    def is_invalid(self, s):
        matches = re.findall(self.pattern, s)
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
    def __init__(self, id, descr, find=None, length=None, **kwargs):
        self.id = id
        self.descr = descr
        self.iff = []
        if 'if' in kwargs:
            if 'length' in kwargs['if']:
                self.iff.append(MinMax(**kwargs['if']['length']))
            if 'pattern' in kwargs['if']:
                self.iff.append(Find(**kwargs['if']['pattern']))

        self.find = Find(**find) if find else None
        self.length = MinMax(**length) if length else None

    def is_applicable(self, s):
        return not any([iff.is_invalid(s) for iff in self.iff])

    def is_invalid(self, s):
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
    def __init__(self, yml):
        self.rules = [Rule(idx + 1, **r) for (idx, r) in enumerate(yml)]  # [:1]

    def is_invalid(self, sentence: str) -> bool:
        for idx, r in enumerate(self.rules):
            if r.is_invalid(sentence):
                # print("RULE %d %s FAILED on |%s|" % (idx, violation, sentence), file=sys.stderr)
                return True
        return False

    def print_rules(self):
        for idx, r in enumerate(self.rules):
            print(idx, "=>", r.__repr__())
