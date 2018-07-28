from ..data import Seed
from ..interfaces import ISaver


class ConsoleSaver(ISaver):
    def __init__(self, **kwargs):
        pass

    def save_seed(self, seed: Seed):
        print('Seed %s' % seed.query)
        print('=' * (len(seed.query) + 5))
        for url in seed.new_links:
            print('   %s' % url)
        print('total: %d' % len(seed.new_links))
        print()
