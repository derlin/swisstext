from typing import List
from mosestokenizer import MosesSentenceSplitter, MosesPunctuationNormalizer
from ..interfaces import ISplitter


class MosesSplitter(ISplitter):
    """
    A splitter using the Moses tool
    `split_sentences.perl <https://github.com/moses-smt/mosesdecoder/blob/master/scripts/ems/support/split-sentences.perl>`_.
    The tool has been wrapped for use from Python, see `mosestokenizer <https://pypi.org/project/mosestokenizer/>`_.

    .. note::
        The language option defines the non-breaking prefixes to use. Here, we use 'de' (German) by default.

    """

    def __init__(self, lang='de', do_norm=False):
        self.lang = lang
        self.norm = MosesPunctuationNormalizer(lang) if do_norm else None
        self.tokenizer = MosesSentenceSplitter(lang)

    def split(self, text: str) -> List[str]:
        """ Split text using Moses. """
        paragraphs = [p for p in text.split('\n') if p and not p.isspace()]
        sentences = []
        for p in paragraphs:
            if self.norm is not None:
                p = self.norm(p)
            sentences.extend(self.tokenizer([p]))
        return sentences