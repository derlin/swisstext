"""
This module defines the generic data structures used across the module / between the different tools.
They have been thought to be decoupled from MongoDB for better flexibility/adaptability.
"""


class Seed:
    """Holds informations on a seed, i.e. a query."""

    def __init__(self, query: str):
        self.query = query  #: the query terms
        self.new_links = []  #: the new links found after the search

    def __repr__(self):
        return "<Seed |%s| (new_links=%d)>" % (self.query, len(self.new_links))
