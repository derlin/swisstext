API Reference
=============

The :mod:`swisstext` namespace contains the following:

* Package :mod:`mongo <swisstext.mongo>`: abstract definitions of the MongoDB structure
* Package :mod:`cmd <swisstext.cmd>`:  impementation of two distinct commandline tools:
   * :mod:`searching <swisstext.cmd.searching>`: discover new URLs from seeds using a Search Engine,
   * :mod:`scraping <swisstext.cmd.scraping>`: scrape the web and discover new Swiss German sentences.
* Package ``frontend``: a Flask application for visualisation and labelling



MongoDB persistence
-------------------

All MongoDB collection definitions.

.. toctree::
   :maxdepth: 10

   swisstext.mongo

Commandline tools
-----------------

Base package for searching and scraping.

.. toctree::
   :maxdepth: 2

   swisstext.cmd


Scraping the web
-----------------

Everything related to scraping the web,
finding new sentences and generating seeds.

.. toctree::
   :maxdepth: 10

   swisstext.cmd.scraping


Making search engine queries
----------------------------

Everything for querying search engines in order to find
new URLs to scrape.

.. toctree::
   :maxdepth: 10

   swisstext.cmd.searching


Parsing Alswiki dumps or text files
------------------------------------

Commandline tools to extract/process sentences from an Alemmanic Wikipedia dump or for processing a text file using the scraping tools (splitter/filter/lid).

.. toctree::
   :maxdepth: 10

   swisstext.alswiki