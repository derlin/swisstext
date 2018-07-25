from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from swisstext.scraping.interfaces import ICrawler
from swisstext.scraping.link_utils import filter_links
import logging

# suppress warning for invalid SSL certificates
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

# define a user-agent other than "python"
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.89 Safari/537.36'}

logger = logging.getLogger(__name__)


class BsCrawler(ICrawler):

    def crawl(self, url: str) -> ICrawler.CrawlResults:
        soup = self._download(url)
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

    def _extract_text(self, soup):
        # see https://stackoverflow.com/a/22800287/2667536
        # kill all script and style elements
        for script in soup(["script", "style"]):
            script.decompose()  # rip it out
        text = soup.get_text()
        # break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # drop blank lines and remove zero-width space
        return "\n".join((chunk.replace(u'\u200B', '') for chunk in chunks if chunk))

    def _extract_links(self, url, soup):
        links = (a.get('href') for a in soup.find_all('a', href=True))
        return [l for l in filter_links(url, links)]
