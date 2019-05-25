from ..interfaces import ISgDetector

import pickle
import re
from os import path
from typing import List

# model information: TfidfVectorizer trained on character n-grams of size 3 to 5, using 6000 features and
# a logistic regression classifier.
_model_file = "swigspot_langid.pickle"
_model_version = 1
_model_version_description = "TfidfVectorizer_ngrams3-5_f6000_logreg"
_model_labels = ['de', 'fr', 'en', 'it', 'sg']

_RR = re.compile("[^\w \.,]|\d|_")  # sanitization regex: remove all but letters, dots and commas


class SwigspotLangid(ISgDetector):
    """
    This LID model was developed during the SwigSpot project.

    In short, it uses 6000 character n-grams features (between 3 and 5 characters long) with TF-IDF scaling
    and a logistic regression. Sentences are preprocessed by removing everything except letters, spaces, commas and dots.

    All the details are available in the
    `SwigSpot repository <https://github.com/derlin/SwigSpot_Schwyzertuutsch-Spotting>`_.
    The notebook for recreating the model is available `here
    <https://github.com/derlin/SwigSpot_Schwyzertuutsch-Spotting/blob/master/language-detection/notebooks/09-FinalModel-SCRAPE.ipynb>`_.

    """

    def __init__(self):
        with open(path.join(path.dirname(path.realpath(__file__)), _model_file), 'br') as f:
            self.pipe = pickle.load(f)

    def predict(self, sentences: List[str]) -> List[float]:
        if sentences is not None and len(sentences) > 0:
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
