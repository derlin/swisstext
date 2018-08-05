"""
This module contains the implementation of a :py:class:`~swisstext.cmd.scraping.interfaces.ICrawler`
that uses BeautifulSoup to extract text and links.
"""
import logging

import requests
from bs4 import BeautifulSoup

from ..interfaces import ICrawler
from ..link_utils import filter_links

# suppress warning for invalid SSL certificates
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

#: Headers passed with each request
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.89 Safari/537.36'}

logger = logging.getLogger(__name__)


class BsCrawler(ICrawler):
    """
    A basic crawler implemented using `BeautifulSoup <https://www.crummy.com/software/BeautifulSoup/bs4/doc/>`_.

    Text is extracted by concatenating all pieces of text (except CSS and script)
    into one string using a space separator (no newlines).


    .. danger::

        This crawler implementation will return the page's textual content in one bulk, with no newlines characters.
        Consequently, results won't be exploitable without a clever
        :py:class:`~swisstext.cmd.scraping.interfaces.ISplitter` (recall that the default implementation split text
        based on newlines...) such as the :py:class:`~swisstext.cmd.scraping.punkt_splitter.PunktSplitter`.

    """

    _joiner = ' '  # used to join text chunks

    def crawl(self, url: str) -> ICrawler.CrawlResults:
        """Extract links and text from a URL."""
        soup: BeautifulSoup = self._download(url)
        return ICrawler.CrawlResults(text=self._extract_text(soup), links=self._extract_links(url, soup))

    def _download(self, url):
        try:
            resp = requests.get(url, verify=False, stream=True, headers=DEFAULT_HEADERS)  # ignore SSL certificates
            # try to avoid encoding issues
            # see https://stackoverflow.com/a/45643551/2667536
            # Note: the encoding might be wrong if the content-type is declaring a charset with
            # uppercase, for example 'text/html; Charset=xxx'. I posted an issue, see
            # https://github.com/requests/requests/issues/4748
            ctype = resp.headers.get('content-type', '').lower()
            if 'html' in ctype or 'text/plain' in ctype:
                encoding = resp.encoding if 'charset' in ctype else None
                # Nice encoding detection, but waaayy to slow
                # http_encoding = resp.encoding if 'charset' in ctype else None
                # html_encoding = EncodingDetector.find_declared_encoding(resp.content, is_html=True)
                # encoding = html_encoding or http_encoding
                return BeautifulSoup(resp.content, 'html.parser', from_encoding=encoding)
            else:
                raise ICrawler.CrawlError("'%s' not HTML (ctype=%s) " % (url, ctype))

        except Exception as e:
            raise ICrawler.CrawlError("'%s' raised an error (%s)" % (url, e)) from e

    def _extract_text(self, soup) -> str:
        # see https://stackoverflow.com/a/22800287/2667536
        # kill all script and style elements
        for script in soup(['script', 'style', 'form']):
            script.decompose()  # rip it out

        # TODO: join with newlines ?
        return self._joiner.join(soup.stripped_strings)

    def _extract_links(self, url, soup):
        links = (a.get('href') for a in soup.find_all('a', href=True))
        return [l for l in filter_links(url, links)]
