"""
This module contains the implementation of a :py:class:`~swisstext.cmd.scraping.interfaces.ICrawler`
that uses BeautifulSoup to extract text and links.
"""
import logging
from typing import List, Generator, Tuple, Union

import requests
from bs4 import BeautifulSoup

from ..interfaces import ICrawler
from swisstext.cmd.link_utils import filter_links

# suppress warning for invalid SSL certificates
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

#: Headers passed with each request
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.89 Safari/537.36'}

#: Timeout used in requests.get
GET_TIMEOUT = 60

logger = logging.getLogger(__name__)


class BsCrawler(ICrawler):
    """
    A basic crawler implemented using `BeautifulSoup <https://www.crummy.com/software/BeautifulSoup/bs4/doc/>`_.

    Text is extracted by concatenating all pieces of text (except CSS and script)
    into one string using a space separator (no newlines).


    .. warning::

        This crawler implementation will return the page's textual content in one bulk, with no newlines characters.
        Consequently, results won't be exploitable without a clever
        :py:class:`~swisstext.cmd.scraping.interfaces.ISplitter` (recall that the default implementation split text
        based on newlines...) such as the :py:class:`~swisstext.cmd.scraping.punkt_splitter.PunktSplitter`.

    .. todo::

        Try using just the response.text from requests to get a proper encoding ?
    """

    def __init__(self, joiner=' '):
        self.joiner = joiner  # used to join text chunks

    def crawl(self, url: str) -> ICrawler.CrawlResults:
        """Extract links and text from a URL."""
        soup, content = self.get_soup(url)
        # get links first, as extract_text_blocks is destructive
        links = self.extract_links(url, soup)
        text_blocks = self.extract_text_blocks(soup)
        return ICrawler.CrawlResults(
            text=self.joiner.join(text_blocks),
            links=links)

    @classmethod
    def get_content(cls, url):
        """Get the HTML content from a URL (as a string), dealing somewhat correctly with encoding."""
        try:
            resp = requests.get(url, verify=False, stream=True, headers=DEFAULT_HEADERS,
                                timeout=GET_TIMEOUT)  # ignore SSL certificates
            content = resp.content  # trigger content decoding to catch ContentDecodingError as well
        except Exception as e:
            # here, don't use from_ex so we can trim the error message
            raise ICrawler.CrawlError(name=e.__class__.__name__, message=str(e)[:50])

        # try to avoid encoding issues
        # see https://stackoverflow.com/a/45643551/2667536
        # Note: the encoding might be wrong if the content-type is declaring a charset with
        # uppercase, for example 'text/html; Charset=xxx'. I posted an issue, see
        # https://github.com/requests/requests/issues/4748
        ctype = resp.headers.get('content-type', '').lower()
        if not ('html' in ctype or 'text/plain' in ctype):
            raise ICrawler.CrawlError(name='CtypeError', message=f'{url} not HTML (ctype={ctype})')

        # also test the .text, so that we avoid returning content with only unprintable chars, e.g. b'\xef\xbb\xbf'
        if len(content) == 0 or len(resp.text.strip()) == 0:
            raise ICrawler.CrawlError(name=f'EmptyDocumentError', message='Content is empty.')

        if 'charset' in ctype: # TODO just return content and let bs4 take care of encoding ?
            ## (1) Nice encoding detection, but waaayy to slow
            # http_encoding = resp.encoding if 'charset' in ctype else None
            # html_encoding = EncodingDetector.find_declared_encoding(resp.content, is_html=True)
            # encoding = html_encoding or http_encoding

            ## (2) another possibility: use the from_encoding argument in BSoup. The problem ? it uses
            # .decode(encoding, 'replace'), which adds strange symbols to the text...

            ## (3) Here, we try another thing: decoding the content by ourselves using the 'ignore' stragegy
            try:
                return content.decode(resp.encoding, 'ignore')
            except LookupError:
                pass  # encoding is unknown, e.g. "none" or ""

        return content

    @classmethod
    def get_soup(cls, url) -> Tuple[BeautifulSoup, Union[bytes,str]]:
        """Get a :py:class:`~bs4.BeautifulSoup` object from a URL (HTML), dealing somewhat correctly with encoding."""
        content = cls.get_content(url)
        return BeautifulSoup(content, 'html.parser'), content

    @classmethod
    def extract_text_blocks(cls, soup) -> Generator[str, None, None]:
        """
        Get text blocks from a :py:class:`~bs4.BeautifulSoup` object.

        .. warning::

            This method is destructive, as it will first remove script, style and forms
            from the HTML/soup object !

        .. todo::

            Find a way to avoid altering the soup object.. ?
        """
        # see https://stackoverflow.com/a/22800287/2667536
        # kill all script and style elements
        for script in soup(['script', 'style', 'form']):
            script.decompose()  # rip it out

        return soup.stripped_strings

    @classmethod
    def extract_links(cls, url, soup):
        """
        Get all links from a soup (a href only).
        Note that links will be resolved (relative to absolute) and filtered (non-HTML removed).
        """
        links = (a.get('href') for a in soup.find_all('a', href=True))
        return [l for l in filter_links(url, links)]


class CleverBsCrawler(BsCrawler):
    """
    Another implementation of the :py:class:`BsCrawler` that tries to be more clever during the text extraction
    step.

    Processing steps:

    1. remove all scripts and CSS content (same as the BsCrawler)
    2. try to detect the page's main content using common naming schemes (``id=main``, ``role=main``, etc).
       If found, stop the processing and return only the text under it.
    3. try to detect and remove the header, footer and navigation before returning the text

    Following those heuristics requires more processing power and might miss some sentences (full sentences
    in the side bar, main content in a poorly-coded website, etc).

    .. todo::

        Make more thorough tests to determine if those heuristics are worth it. If so, make this implementation
        the default.

    """
    _main_selectors = ['[role=main]'] + \
                      [s
                       for name in ['main', 'main-content', 'mainContent', 'MainContent', 'wrapper']
                       for s in [f".{name}", f"#{name}"]]

    _exclude_selectors = ','.join(['header', '#header', 'footer', '#footer', '[role=footer]', '[role=navigation]'])

    def extract_text_blocks(self, soup) -> Generator[str, None, None]:

        for script in soup(['script', 'style']):
            script.decompose()  # rip it out

        # try to extract main content
        for selector in self._main_selectors:
            main = soup.select(selector)
            if len(main) == 1:
                return main[0].stripped_strings

        # no main content found... try to remove header and footer
        for part in soup.select(self._exclude_selectors):
            part.decompose()

        return soup.stripped_strings
