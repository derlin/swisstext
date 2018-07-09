from typing import List
from nltk.tokenize.punkt import PunktSentenceTokenizer
from swisstext.interfaces import ISplitter


class PunktSplitter(ISplitter):

    def __init__(self):
        self.tokenizer = PunktSentenceTokenizer()

    def split(self, text: str) -> List[str]:
        return self.tokenizer.tokenize(text)
