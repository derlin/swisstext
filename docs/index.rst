.. SwissText documentation master file, created by
   sphinx-quickstart on Tue Aug  7 15:30:19 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to SwissText's documentation!
=====================================

.. toctree::
   :maxdepth: 2
   :caption: Getting started:

   installation
   usage


See also :mod:`swisstext.cmd` for usage examples.


API documentation overview
===========================


The :mod:`swisstext` namespace contains the following:

* Package :mod:`mongo <swisstext.mongo>`: abstract definitions of the MongoDB structure
* Package :mod:`cmd <swisstext.cmd>`:  impementation of two distinct commandline tools:
   * :mod:`searching <swisstext.cmd.searching>`: discover new URLs from seeds using a Search Engine,
   * :mod:`scraping <swisstext.cmd.scraping>`: scrape the web and discover new Swiss German sentences.
* Package ``frontend``: a Flask application for visualisation and labelling


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
