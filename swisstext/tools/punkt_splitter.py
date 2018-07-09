from typing import List
from nltk.tokenize.punkt import PunktSentenceTokenizer
from swisstext.interfaces import ISplitter


class PunktSplitter(ISplitter):

    def __init__(self):
        self.tokenizer = PunktSentenceTokenizer()

    def split(self, text: str) -> List[str]:
        paragraphs = [p for p in text.split('\n') if p]
        sentences = []
        for p in paragraphs:
            sentences.extend(self.tokenizer.tokenize(p))
        return sentences