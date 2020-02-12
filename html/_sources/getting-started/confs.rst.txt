======================
Configuration options
======================

The behavior of the scraper highly depends on the tools chosen, which is defined in a configuration YAML file (see :py:mod:`swisstext.cmd.base_config`).

Some tool options are more suited together, so in this section I try to detail some of the tips and tricks to get the best system.


Current ?best? pipeline configuration
======================================

Using default tools
-------------------

The current best configuration for Swiss-German spotting is the following:

.. code-block:: yaml

    # scraping
    pipeline:
      crawler: .JustextCrawler
      normalizer: .Normalizer
      splitter: .MocySplitter
      sentence_filter: .PatternSentenceFilter
      sg_detector: .SwigspotLangid
      decider: .OneNewSgDecider
      saver: .MongoSaver

    crawler_options:
      keep_bad: false

    normalizer_options:
      fix_encoding: true
      strip_emojis: false

    splitter_options:
      more: true
      keep_newlines: true

    # searching
    search_engine:
      query_builder: .QuoteWordsQueryBuilder
      saver: .MongoSaver
      searcher: .StartPageGeneratorFactory

The :py:class:`~swisstext.cmd.scraping.tools.justext_crawler.JustextCrawler` is quite efficient at extracting *and*
classifying paragraphs of text. Using the ``keep_bad`` option, we discard paragraphs such as short titles, breadcrumbs,
post meta, etc. Setting ``keep_bad`` to true should impact the pipeline much, assuming the filter does its job properly.

Then, the :py:class:`~swisstext.cmd.scraping.tools.norm_punc.Normalizer`
will take care of unifying unicode. The ``fix_encoding`` option is important, as many GSW sentences
are found on old forums with databases improperly configured
(e.g. `celica-t23.ch <http://www.celica-t23.ch/new/wbb2/thread.php?threadid=3566>`_ uses twos encodings ...).
However, the ``strip_emojis`` option is set to false, because it adds a *huge* overhead for little outcome (not so many pages have unicode emojis). The only downside is that it messes with the splitter, which is not able to properly segment sentences when emojis are present.


The best splitter so far is the :py:class:`~swisstext.cmd.scraping.tools.mocy_splitter.MocySplitter`, an improvement
upon Moses ``split-sentences.perl``. Note that *using a normalizer is vital* for it to work well,
since the splitter is not configured to handle all possible space/dash/etc. unicode codepoints.
The ``more`` option will split cleverly on ``:;`` (here, no real arguments, just a matter of taste).
The ``keep_newlines`` option is really interesting, but *only in conjunction with the JustextCrawler*:
justext already returns paragraphs delimited by newlines, so it is better to keep those newlines and thus avoid to
combine a title or a button text (both lacking punctuation) with a content.
To see the difference, try crawling `twitter <https://twitter.com/agnesiumm/status/1171531642969546757?lang=en-gb>`_
with and without ``keep_newlines`` ! Without, we will basically crawl all possible versions of a page (different ``lang=xxx``) and always find new sentences because button texts are appended and change depending on the language...

The rest of the tools are less critical and their behavior is not impacted by the behavior of the previous tools.


Using extra tools
------------------

.. code-block:: yaml

    # scraping
    pipeline:
      crawler: .JustextCrawler
      normalizer: .Normalizer
      splitter: .MocySplitter
      sentence_filter: .PatternSentenceFilter
      decider: decider.Decider
      url_filter: extra.sg_url_filter.SgUrlFilter
      sg_detector: extra.bert_torch_predictor.BertPredictor

    crawler_options:
      keep_bad: false

    normalizer_options:
      fix_encoding: true
      strip_emojis: true

    splitter_options:
      keep_newlines: true
      more: true

    sg_detector_options:
      chunk_size: 1000

    # searching
    search_engine:
      query_builder: .QuoteWordsQueryBuilder
      saver: .MongoSaver
      searcher: .StartPageGeneratorFactory

    # general options
    options:
      crawl_depth: 3
      max_fetches: -1
      max_results: 20
      min_proba: 0.92
      num_workers: 3

The big difference here is the use of a custom URL filter, decider and language detector. More precisely:

1. *URL filter*: the ``extra`` directory contains a specific implementation of URL filter that deals with some of GSW blogs that have strange URL patterns. It ensures we do not scrape for nothing by blacklisting some and normalizing others;
2. *SG detector*: we use a better language identifier, a BERT model that was finetuned on the task of language identification; The model is available in another repo, the code in ``extra`` is just a wrapper around it to make it compatible with swisstext;
3. *decider*: the decider implementation varies depending on the needs. On our latest runs to find Swiss German quickly, we used the following:

.. code-block:: python

    class Decider(BasicDecider):

        def should_page_be_crawled(self, page: Page) -> bool:
            """Returns true only if the page is new."""
            return page.is_new()


        def should_children_be_crawled(self, page: Page) -> bool:
            if super().should_children_be_crawled(page):
                # just don't try going further if no new sg is found
                return len(page.new_sg) > 2

More information can be found in our publication:
`Automatic Creation of Text Corpora for Low-Resource Languages from the Internet: The Case of Swiss German <https://arxiv.org/abs/1912.00159>`_.

Tool dependencies
==================

* splitters don't work well without normalization of the text as they are made to work with the basic character set (vs all the unicode variations);
* ``MocySplitter.keep_newlines`` option should be used only in conjunction with ``JustextCrawler`` (and the default joiner);

