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
        self.do_norm = do_norm

    def split(self, text: str) -> List[str]:
        """ Split text using Moses. """
        paragraphs = [p for p in text.split('\n') if p and not p.isspace()]
        sentences = []

        # ensure to create a new toolwrapper each time for multithreading purpose
        # without this, random deadlocks will occur when num_workers > 1
        norm = MosesPunctuationNormalizer(self.lang) if self.do_norm else None
        with MosesSentenceSplitter(self.lang) as tokenizer:
            for p in paragraphs:
                if norm is not None:
                    p = norm(p)
                sentences.extend(tokenizer([p]))
        if norm is not None: norm.close()

        return sentences
