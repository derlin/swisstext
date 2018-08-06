"""
This package contains everything for running the SwissText Scraping logic.

It is implemented using two command-line programs, each in its own package:

* ``st_scrape`` defined in :py:mod:`swisstext.cmd.scraping`, is used to scrape URLs and detect/save Swiss German sentences,
* ``st_search`` defined in :py:mod:`swisstext.cmd.searching`, is used to do submit search queries using seeds and gather
    new URLs to scrape

After installing the package, here is an example use:

.. code-block:: bash

    ## To use this script, create a directory and create the following files:
    ##  * configuration files: searching.yaml and scraping.yaml (see the doc)
    ##  * bootstrap files: base_seeds.txt, one seed per line to start with

    set -e
    trap exit SIGINT

    base_dir=.  # relative link to the base directory

    st_search="st_search -c $base_dir/searching.yaml"
    st_scrape="st_scrape -c $base_dir/scraping.yaml"

    # search for the bootstrap seeds
    $st_search from_file $base_dir/base_seeds.txt

    # do five loops. Each loop: (a) scrapes the new URLs, (b) generates random seeds, (c) use the new seeds
    for i in $(seq 1 5); do
        echo "======= START LOOP"
        # scrape at most 30 new urls
        $st_scrape --no-seed from_mongo --new -n 30
        echo "======= generating SEEDS"
        # generate three random seeds, each time from 150 randomly picked sentences
        $st_scrape gen_seeds -s 150 -n 1
        $st_scrape gen_seeds -s 150 -n 1
        $st_scrape gen_seeds -s 150 -n 1
        echo "======= searching SEEDS"
        # search URLs using the newly generated seeds
        $st_search from_mongo --new -n 3
    done

.. todo:: add pipeline schema

"""