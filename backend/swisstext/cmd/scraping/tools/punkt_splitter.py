from typing import List
from nltk.tokenize.punkt import PunktSentenceTokenizer
from ..interfaces import ISplitter


class PunktSplitter(ISplitter):
    """
    A splitter using the
    `PunktSentenceTokenizer <https://www.nltk.org/api/nltk.tokenize.html#module-nltk.tokenize.punkt>`_, the NLTK
    implementation of the "Unsupervised Multilingual Sentence Boundary Detection (Kiss and Strunk (2005)" algorithm.

    .. note::
        The default implementation uses a model trained on English sentences.
        `This kaggle resource <https://www.kaggle.com/nltkdata/punkt/version/2#>`_ offers
        pretrained Punkt Models for other languages as well, including German. In my tests though, German models
        performed poorly compared to the default...

    .. todo::
        Train a Punkt model for Swiss-German.
    """

    def __init__(self):
        self.tokenizer = PunktSentenceTokenizer()

    def split(self, text: str) -> List[str]:
        paragraphs = (p for p in text.split('\n') if p)
        sentences = []
        for p in paragraphs:
            sentences.extend(self.tokenizer.tokenize(p))
        return sentences