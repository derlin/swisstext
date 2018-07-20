#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from swisstext.scraping.interfaces import ISeedCreator

import logging
from sklearn.feature_extraction.text import CountVectorizer

from typing import List, Tuple

logger = logging.getLogger(__file__)


class BasicSeedCreator(ISeedCreator):
    def __init__(self, ngram_range=(3, 3)):
        self.ngram_range = ngram_range

    def generate_seeds(self, sentences: List[str], max=10, stopwords: List[str] = list()) -> List[str]:
        counts = self._get_ngrams(sentences, stopwords)
        return [t[1] for t in counts[:max]]

    def _get_ngrams(self, sentences, stopwords: List[str]) -> List[Tuple[float, str]]:
        vectorizer = CountVectorizer(ngram_range=self.ngram_range, stop_words=stopwords)
        n_grams = vectorizer.fit_transform(sentences)
        vocab = vectorizer.vocabulary_
        count_values = n_grams.toarray().sum(axis=0)
        return sorted([(count_values[i], k) for k, i in vocab.items()], reverse=True)


if __name__ == "__main__":
    sentences = [l.strip()[1:-1] for l in open('/tmp/st1_mongo_3levels_17336_sentences/sentences_only.csv')][1:]
    sc = BasicSeedCreator()
    seeds = sc.generate_seeds(sentences, max=100)
    print("\n".join(seeds))