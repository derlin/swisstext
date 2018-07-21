import click

from swisstext.searching.config import Config
from swisstext.searching.data import Seed
from swisstext.searching.interfaces import ISearcher
from swisstext.searching.tools.start_page import StartPageGeneratorFactory


@click.command()
@click.option('-c', '--config', type=click.Path(dir_okay=False), default=None)
@click.argument('seedsfile', type=click.File('r'))
def run(config, seedsfile):
    # one thread, 18 urls = ~ 30 seconds
    import time
    start = time.time()

    conf = Config() if config is None else Config(config)

    engine = conf.create_search_engine()
    seeds = [Seed(l.strip()) for l in seedsfile if l]

    engine.process(seeds, max_results=conf.options.max_results)

    stop = time.time()
    print("Done. It took {} seconds.".format(stop - start))

if __name__ == "__main__":
    run()
