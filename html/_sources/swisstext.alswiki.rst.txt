AlsWiki dumps parser
=========================

.. automodule:: swisstext.alswiki
    :members:
    :undoc-members:
    :show-inheritance:

Commandline
-----------

Use ``st_alswiki -h`` to discover all the capabilities of the tool.

.. code-block:: text

    Usage: st_alswiki [OPTIONS] COMMAND [ARGS]...

      A suite of tools for downloading, parsing and processing wikipedia dumps.

    Options:
      -l, --log-level [debug|info|warning|fatal]
      -h, --help                      Show this message and exit.

    Commands:
      download  Download the latest dump of als.wikipedia.org.
      parse     Extract articles from a wiki dump.
      process   Process articles using the scraping pipeline.
      txt       Process a text file.


Alswiki dumps
-------------

If you want to add the sentences from an alswiki dump to the mongo database, you can use:

.. code-block:: bash

    st_alswiki download
    st_alsiwiki parse alswiki-latest-pages-articles.xml.bz2
    st_alswiki process alswiki-20190101-pages-articles.json.bz2

Remember that by default, the scraping pipeline is configured to use MongoDB on localhost. If you would rather get the output into a file, just pass a custom ``config.yaml`` file to the ``process`` subcommand using the ``-c`` option.

.. code-block:: yaml

    # custom config: output the results to stdout
    pipeline:
      saver: .console_saver.ConsoleSaver

    saver_options:
      # where to save the output (default to stdout)
      sentences_file: alswiki_sentences.txt

.. note::

    For old dumps with older XML syntax, you can use `WikiExtractor.py  <https://github.com/attardi/wikiextractor>`_ to extract text from the dumps, get the text from the JSON file and then use the txt subcommand.

Processing text files
---------------------

The ``alswiki txt`` subcommand will use only a subpart of the pipeline. It will use:

1. *splitter*: split text into sentences
2. *filter*: filter out ill/invalid sentences
3. *language id*: filter out non Swiss German sentences

And write the results to stdout.

The configuration file is the same as the scraping tool, so it is possible to select which tool implementation to use. To skip any of the above steps, create a custom configuration and:

* for 1. and 2., specify the interface in the configuration pipeline
* for 3., set the ``option.min_proba`` to 0 in the configuration

For example, this configuration will do nothing:

.. code-block:: yaml

    # turn off EVERY TOOl (hence doing nothing)

    pipeline:
        splitter: swisstext.cmd.scraping.interfaces.ISplitter
        sentence_filter: swisstext.cmd.scraping.interfaces.ISentenceFilter

    options:
      min_proba: 0.85