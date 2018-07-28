from ..interfaces import ISgDetector

import pickle
import re
from os import path
from typing import List

_model_file = "swigspot_langid.pickle"
_model_version = 1
_model_version_description = "TfidfVectorizer_ngrams3-5_f6000_logreg"
_model_labels = ['de', 'fr', 'en', 'it', 'sg']

_RR = re.compile("[^\w \.,]|\d|_")


class SwigspotLangid(ISgDetector):

    def __init__(self):
        with open(path.join(path.dirname(path.realpath(__file__)), _model_file), 'br') as f:
            self.pipe = pickle.load(f)

    def predict(self, sentences: List[str]) -> List[float]:
        if sentences:
            san = (self.sanitize(s) for s in sentences)
            return [proba[4] for proba in self.pipe.predict_proba(san)]
        else:
            return []

    def sanitize(self, s: str) -> str:
        san = s.lower()
        san = re.sub(_RR, "", san)
        san = re.sub(" +", " ", san)
        san = re.sub(" \.", ".", san)
        return san.strip()
