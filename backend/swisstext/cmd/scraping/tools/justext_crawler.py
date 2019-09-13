"""
This module contains a subclass of :py:class:`~.bs_crawler.BsCrawler`
relying on `JusText <https://github.com/miso-belica/jusText>`_ for text extraction.

It seems to work better than :py:class:`~.bs_crawler.BsCrawler` or :py:class:`~.bs_crawler.CleverBsCrawler`.
To get a feel, try the `online demo of the original JustText <http://nlp.fi.muni.cz/projects/justext/>`_.

.. note::

    * usually, jusText uses ``''`` (empty string) to join text nodes inside a paragraph, thus making things like
      "*One sentence.Second sentence*" likely. Here, we always use a space to join, then normalize the spaces.
    * justext will throw an error on an empty document content, which is wrapped inside a
      :py:class:`~swisstext.cmd.scraping.interface.ICrawler.CrawlError`.

"""
import argparse
import logging
import re

import justext
from swisstext.cmd.scraping.interfaces import ICrawler
from swisstext.cmd.scraping.tools import BsCrawler

logger = logging.getLogger(__name__)


class JustextCrawler(BsCrawler):
    """
    A :py:class:`~.bs_crawler.BsCrawler` that relies on
    `JusText <https://github.com/miso-belica/jusText>`_ to cleverly extract meaningful text from webpages.
    """

    def __init__(self, joiner='\n',
                 keep_bad=True,
                 stoplist=None,
                 stopwords_low=justext.core.STOPWORDS_LOW_DEFAULT,
                 stopwords_high=justext.core.STOPWORDS_HIGH_DEFAULT,
                 **kwargs):
        """
        Create a crawler instance.
        :param joiner: character used to join paragraphs;
        :param keep_bad: if set, keep everything.
        If unset, keep only paragraphs with a context-free class of "neargood" or "good".
        :param stoplist: see the `justText doc <https://github.com/miso-belica/jusText/blob/dev/doc/algorithm.rst>`_
        :param stopwords_low: idem
        :param stopwords_high: idem
        :param kwargs: unused
        """
        super().__init__(joiner=joiner)

        if stoplist is not None:
            with open(stoplist) as f:
                self.kwargs = dict(
                    stoplist=set(l.strip() for l in f if len(l)),
                    stopwords_low=stopwords_low,
                    stopwords_high=stopwords_high)
        else:
            self.kwargs = dict(stoplist=set(), stopwords_low=0, stopwords_high=0)

        self.kwargs.update(kwargs)
        self.keep_bad = keep_bad
        logger.debug(self)

    def crawl(self, url: str):
        soup, content = self.get_soup(url)
        # For links, use bs4 (easier)
        links = self.extract_links(url, soup)

        try:
            # justext uses the decode/replace strategy by default, so encoding errors shouldn't happen
            # see justext core.py:DEFAULT_ENC_ERRORS
            paragraphs = justext.justext(content, encoding=soup.original_encoding, **self.kwargs)
            text_blocks = (self._get_text(p) for p in paragraphs if self._paragraph_ok(p))
            return ICrawler.CrawlResults(
                text=self.joiner.join(text_blocks),
                links=links)
        except Exception as e:
            if 'Document is empty' in str(e):
                # might happen if the content is not HTML/has no tags
                raise ICrawler.CrawlError(name='JustextError', message=str(e))
            raise e

    def _get_text(self, p):
        # mmhh... In justext, they join on '', such that we often have things like:
        # "end of sentence.Start of sentence".
        text = ' '.join(p.text_nodes).replace('\n', ' ')
        return re.sub(' +', ' ', text).strip()

    def _paragraph_ok(self, p):
        # look at context-free and accept neargood as well
        # "good" class may be skipped because the cf class is "short" (titles)
        return self.keep_bad or 'good' in p.cf_class
        # return self.keep_bad or p.class_type != 'bad'

    def __str__(self):
        return f'Justext({vars(self)})'.replace("'", '')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url', nargs='+')
    parser.add_argument('-joiner', default='\n')
    parser.add_argument('-good', default=False, action='store_true', help='Keep only good|neargood sentences.')
    args = parser.parse_args()

    jt = JustextCrawler(joiner=args.joiner, keep_bad=not args.good)

    for url in args.url:
        try:
            res = jt.crawl(url)
            print(f'==== {url}')
            print(res.text)
        except Exception as e:
            print(e)
            # raise e
