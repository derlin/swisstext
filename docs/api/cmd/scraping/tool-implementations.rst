======================
Tool implementations
======================

.. automodule:: swisstext.cmd.scraping.tools
    :members:
    :undoc-members:
    :show-inheritance:


Deciders
==============================

.. automodule:: swisstext.cmd.scraping.tools.basic_decider
    :members:
    :undoc-members:
    :show-inheritance:

Seed creators
==============================

.. automodule:: swisstext.cmd.scraping.tools.basic_seed_creator
    :members:
    :undoc-members:
    :show-inheritance:

Crawlers
==============================

.. automodule:: swisstext.cmd.scraping.tools.bs_crawler
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: swisstext.cmd.scraping.tools.justext_crawler
    :members:
    :undoc-members:
    :show-inheritance:

Normalizers
==============================

.. automodule:: swisstext.cmd.scraping.tools.norm_punc
    :members:
    :undoc-members:
    :show-inheritance:

Splitters
==============================

.. automodule:: swisstext.cmd.scraping.tools.punkt_splitter
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: swisstext.cmd.scraping.tools.moses_splitter
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: swisstext.cmd.scraping.tools.mocy_splitter
    :members:
    :undoc-members:
    :show-inheritance:


Sentence Filters
==============================

.. automodule:: swisstext.cmd.scraping.tools.pattern_sentence_filter
    :members: PatternSentenceFilter
    :undoc-members:
    :show-inheritance:

Link Filters
==============================

It is optionally possible to add a custom URL filtering logic that will be called for each new URL found on a page.

This let's you:

1. ignore child URLs (by returning ``None``) or
2. modify child URLs, for example by normalizing subdomains, stripping url parameters, etc.

Just create an instance of the :py:class:`~swisstext.cmd.scraping.interfaces.IUrlFilter` interface and implement its ``fix`` method.

Language Detectors
==============================

.. automodule:: swisstext.cmd.scraping.tools.swigspot_langid
    :members:
    :undoc-members:
    :show-inheritance:

Savers
==============================

.. automodule:: swisstext.cmd.scraping.tools.console_saver
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: swisstext.cmd.scraping.tools.mongo_saver
    :members:
    :undoc-members:
    :show-inheritance:

