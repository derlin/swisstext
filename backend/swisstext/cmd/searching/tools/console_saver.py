from ..data import Seed
from ..interfaces import ISaver


class ConsoleSaver(ISaver):
    """
    Implementation of an :py:class:`~swisstext.cmd.searching.interfaces.ISaver` useful for testing and debugging.
    It does not persist any results, but prints everything to the console instead.
    """

    def __init__(self, **kwargs):
        pass

    def save_seed(self, seed: Seed):
        print('Seed %s' % seed.query)
        print('=' * (len(seed.query) + 5))
        for url in seed.new_links:
            print('   %s' % url)
        print('total: %d' % len(seed.new_links))
        print()
