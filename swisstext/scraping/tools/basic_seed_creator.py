#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from swisstext.scraping.interfaces import ISeedCreator

import logging

import re
from typing import List, Tuple

logger = logging.getLogger(__file__)


# TODO use a generator instead ?
class BasicSeedCreator(ISeedCreator):
    def __init__(self, ngram_range=(3, 3)):
        self.ngram_range = ngram_range

    def generate_seeds(self, sentences: List[str], max=10, stopwords: List[str] = list()) -> List[str]:
        counts = self._get_ngrams(sentences, stopwords)
        return [t[1] for t in counts[:max]]

    def _get_ngrams(self, sentences, stopwords: List[str]) -> List[Tuple[float, str]]:
        from sklearn.feature_extraction.text import CountVectorizer
        vectorizer = CountVectorizer(ngram_range=self.ngram_range, stop_words=stopwords)
        n_grams = vectorizer.fit_transform(sentences)
        vocab = vectorizer.vocabulary_
        count_values = n_grams.toarray().sum(axis=0)
        return sorted([(count_values[i], k) for k, i in vocab.items()], reverse=True)


class IdfSeedCreator(ISeedCreator):
    def __init__(self, sanitize=True, **kwargs):
        self.sanitize = sanitize
        self.kwargs = dict(ngram_range=(3, 3), use_idf=True, sublinear_tf=True)
        self.kwargs.update(kwargs)

    def generate_seeds(self, sentences: List[str], max=10, stopwords: List[str] = list()) -> List[str]:
        if sentences:
            counts = self._get_ngrams(sentences, stopwords)
            return [t[1] for t in counts[:max]]
        else:
            logger.warning("No sentences...")
            return []

    def _get_ngrams(self, sentences, stopwords: List[str]) -> List[Tuple[float, str]]:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer(**self.kwargs, stop_words=stopwords)
        if self.sanitize:
            sentences = (re.sub("(^|\W)\d+($|\W)", " ", line) for line in sentences)
        words = vectorizer.fit_transform(sentences)
        vocab = vectorizer.vocabulary_
        count_values = words.toarray().sum(axis=0)
        return sorted([(count_values[i], k) for k, i in vocab.items()], reverse=True)