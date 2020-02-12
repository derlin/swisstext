import re

from ..interfaces import IQueryBuilder


class QuoteQueryBuilder(IQueryBuilder):
    """Add double quotes around the whole query."""

    def prepare(self, query: str, **kwargs):
        return f'"{query.strip()}"'


class QuoteWordsQueryBuilder(IQueryBuilder):
    """Add double quotes around each word in the query."""

    def prepare(self, query: str, **kwargs):
        return ' '.join(f'"{w}"' for w in re.split('\s+', query))
