=================
swisstext.alswiki
=================

.. automodule:: swisstext.alswiki
    :members:
    :undoc-members:
    :show-inheritance:


The magic happens by calling ``st_alswiki``.

.. click:: swisstext.alswiki.commandline:cli
  :prog: st_alswiki
  :show-nested:

Processing Alswiki dumps
------------------------

If you want to add the sentences from an alswiki dump to the mongo database, you can use:

.. code-block:: bash

    st_alswiki download
    st_alswiki parse alswiki-latest-pages-articles.xml.bz2
    st_alswiki process alswiki-latest-pages-articles.json.bz2

Remember that by default, the scraping pipeline is configured to use MongoDB on localhost.
If you would rather get the output into a file, just pass a custom ``config.yaml`` file to
the ``process`` subcommand using the ``-c`` option.

.. code-block:: yaml

    # custom config: output the results to stdout
    pipeline:
      saver: .console_saver.ConsoleSaver

    saver_options:
      # where to save the output (default to stdout)
      sentences_file: alswiki_sentences.txt

.. note::

    For old dumps with older XML syntax, you can use `WikiExtractor.py  <https://github.com/attardi/wikiextractor>`_
    to extract text from the dumps, get the text from the JSON file and then use the txt subcommand.

Processing text files
---------------------

The ``alswiki txt`` subcommand will use only a subpart of the pipeline. It will use:

1. *splitter*: split text into sentences
2. *filter*: filter out ill/invalid sentences
3. *language id*: filter out non Swiss German sentences

And write the results to stdout.

The configuration file is the same as the scraping tool (see :mod:`st_scrape config <swisstext.cmd.scraping.config>`),
so it is possible to select which tool implementation to use.
To skip any of the above steps, create a custom configuration and:

* for 1. and 2., specify the interface in the configuration pipeline or use the special ``_I_`` magic;
* for 3., set the ``options.min_proba`` to 0 in the configuration (or set the ``sg_detector`` to the interface);

For example, this configuration will do nothing:

.. code-block:: yaml

    # turn off EVERY TOOl (hence doing nothing)

    pipeline:
        splitter: swisstext.cmd.scraping.interfaces.ISplitter # or _I_
        sentence_filter: swisstext.cmd.scraping.interfaces.ISentenceFilter # or _I_

    options:
      min_proba: 0.0