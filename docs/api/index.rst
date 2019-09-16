=============
API Overview
=============

The :mod:`swisstext` namespace contains the following:

- Package :mod:`mongo <swisstext.mongo>`: abstract definitions of the MongoDB structure;
- Package :mod:`cmd <swisstext.cmd>`:  impementation of two distinct commandline tools:

   * :mod:`searching <swisstext.cmd.searching>`: discover new URLs from seeds using a Search Engine;
   * :mod:`scraping <swisstext.cmd.scraping>`: scrape the web and discover new Swiss German sentences;

- Package ``frontend``: a Flask application for visualisation and labelling;
- Package :mod:`alswiki <swisstext.cmd.alswiki>`: a commandline tool to extract sentences from wikipedia dumps.

.. toctree::
    :caption: packages
    :maxdepth: 1

    cmd/package
    cmd/scraping/package
    cmd/searching/package
    mongo/package
    alswiki/package