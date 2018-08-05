"""
This module contains multiple :py:class:`~swisstext.cmd.scraping.interfaces.ISeedCreator` implementations.
They all use sklearn vectorizers (word N-grams) under the hood.
"""

from ..interfaces import ISeedCreator

import logging

import re
from typing import List, Tuple

logger = logging.getLogger(__file__)


# TODO use a generator instead ?
class BasicSeedCreator(ISeedCreator):
    """
    A basic seed creator that uses an sklearn ``CountVectorizer`` to compute frequent word N-grams.
    The generated seeds are simply the x most frequent N-grams found.
    """

    def __init__(self, ngram_range=(3, 3)):
        self.ngram_range = ngram_range  #: ngram range parameter passed to the CountVectorizer

    def generate_seeds(self, sentences: List[str], max=10, stopwords: List[str] = None) -> List[str]:
        """Return a list of seeds composed of the most frequent n-grams."""
        counts = self._get_ngrams(sentences, stopwords)
        return [t[1] for t in counts[:max]]

    def _get_ngrams(self, sentences, stopwords: List[str]) -> List[Tuple[float, str]]:
        """Return a sorted array of (frequency, n-grams)"""
        from sklearn.feature_extraction.text import CountVectorizer
        vectorizer = CountVectorizer(ngram_range=self.ngram_range, stop_words=stopwords or [])
        n_grams = vectorizer.fit_transform(sentences)
        vocab = vectorizer.vocabulary_
        count_values = n_grams.toarray().sum(axis=0)
        return sorted([(count_values[i], k) for k, i in vocab.items()], reverse=True)


class IdfSeedCreator(ISeedCreator):
    """
    A basic seed creator that uses an sklearn ``TfidfVectorizer`` to compute frequent word N-grams.
    The generated seeds are the x n-grams with the highest score.
    """

    def __init__(self, sanitize=True, **kwargs):
        self.sanitize = sanitize
        """
        If this flag is set, digits that are not part of a word will be removed before feeding the 
        vectorizer. This is useful because the ``TfidfVectorizer``'s default token pattern considers
        digits as actual words (but ignores punctuation, 
        see `the CountVectorizer token_pattern attribute
        <https://github.com/scikit-learn/scikit-learn/blob/master/sklearn/feature_extraction/text.py>`_).
        """
        self.kwargs = dict(ngram_range=(3, 3), use_idf=True, sublinear_tf=True)
        """The arguments to pass to the vectorizer. They can be overriden in the constructor."""
        self.kwargs.update(kwargs)

    def generate_seeds(self, sentences: List[str], max=10, stopwords: List[str] = None) -> List[str]:
        """Return a list of seeds composed of the most frequent n-grams (ponderated by IDF)."""
        if sentences:
            counts = self._get_ngrams(sentences, stopwords)
            return [t[1] for t in counts[:max]]
        else:
            logger.warning("No sentences...")
            return []

    def _get_ngrams(self, sentences, stopwords: List[str]) -> List[Tuple[float, str]]:
        # train the vectorizer and extract the ordered list of ngrams+scores
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer(**self.kwargs, stop_words=stopwords)
        if self.sanitize:
            sentences = (re.sub("(^|\W)\d+($|\W)", " ", line) for line in sentences)
        words = vectorizer.fit_transform(sentences)
        vocab = vectorizer.vocabulary_
        count_values = words.toarray().sum(axis=0)
        return sorted([(count_values[i], k) for k, i in vocab.items()], reverse=True)
