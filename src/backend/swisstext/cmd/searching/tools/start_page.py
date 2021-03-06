"""
This module implements an :py:mod:`~swisstext.cmd.searching.interfaces.ISearcher` using
`<http://startpage.com/>`_.

.. warning::
    This module highjacks startpage.com !! There are no API available, so this is really a dirty
    hack. But we couldn't find free APIs to run tests... So use this module sparsely and
    **ONLY IN DEVELOPMENT**. We decline all responsibility in case startpage detects the robot...
"""
import logging
import re
from typing import List, Dict, Iterable, Optional

import requests
from bs4 import BeautifulSoup as Soup
import urllib.parse as up

# link to the search startpage
from ..interfaces import ISearcher

_SEARCH_LINK = "https://www.startpage.com/do/asearch"
# parameters for the first search query
# the only missing parameter is: query=<thing to search>
# DEFAULT_PARAMS = dict(hmb=1, cat='web', cmd='process_search', engine0='v1all', abp=1, t='air', nj=0)
_DEFAULT_PARAMS = dict(cat='web', cmd='process_search', dgf=1, hmb=1, pl="", ff="")
# CSS selector used to retrieve all the results links from startpage
_RESULT_LINK_CSS_SELECTOR = 'a[class$="result-url"]'

# regex excluding some URLs we know are not interested
excludes = [
    'www.youtube.com',
    '\.pdf$',
    '\.docx?$',
]

logger = logging.getLogger(__name__)


class StartPageGenerator(Iterable[str]):
    """
    A new generator is created for each query. Its usage is similar to the generator described in the
    :py:mod:`~swisstext.cmd.searching.tools.google_search` module.
    """

    def __init__(self, query):
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
        }
        self._params = dict(**_DEFAULT_PARAMS, query=query)  #: parameters for the first search
        self._current_results: List[str] = []  # list of links found on the current page and not yet consumed
        self._current_page = 0  # counter that reflects the current page we are returning the results from
        self._has_next = True  # true if there is a next page
        self._next_page_form: Optional[Dict] = None  # keep track of the parameters for fetching the next page

    def __iter__(self):
        return self

    def __next__(self) -> str:
        if not self.has_next():
            raise StopIteration
        return self._current_results.pop()

    def next(self) -> str:
        return self._current_results.pop()

    def has_next(self) -> bool:
        if len(self._current_results) == 0 and self._has_next:
            self._fetch_next()
        return len(self._current_results) > 0

    def _fetch_next(self):
        if not self._has_next:
            return

        if self._current_page == 0:
            assert self._next_page_form is None, f'Page is 0 but _form is not None'
            # first request, do a simple get to fetch page 1
            r = requests.get(_SEARCH_LINK, params=self._params, headers=self._headers)
            self._next_page_form = {}
        else:
            assert self._next_page_form is not None, f'There is no form, but page counter is at {self._current_page}'
            # not the first request, use a POST with the navigation form
            r = requests.post(self._next_page_form['url'], data=self._next_page_form['data'], headers=self._headers)

        # update page
        self._current_page += 1
        logger.debug(f'Fetched page {self._current_page}')

        # get data
        soup = Soup(r.text, 'html.parser')
        self._current_results.extend(self._get_links(soup))

        # get the navigation form for further queries
        forms = soup.select(f'form:has(input[name="page"][value="{self._current_page + 1}"])')
        if len(forms) == 0:
            # not more data
            self._has_next = False
            logger.debug(f'Page {self._current_page} is the last one.')
        else:
            self._next_page_form['url'] = up.urljoin(_SEARCH_LINK, forms[0]['action'])
            form_data = [(hidden['name'], hidden['value']) for hidden in forms[0].select('input[type=hidden]')]
            self._next_page_form['data'] = dict(form_data)
            assert 'page' in self._next_page_form['data'] and \
                   int(self._next_page_form['data']['page']) == self._current_page + 1

    def _get_links(self, soup: Soup) -> List[str]:
        """
        For each result in the page, extract the link it is pointing to.
        :param soup: a BeautifulSoup object with the HTML page
        :return: a list of links
        """
        logger.debug("getting links...")
        results = [l['href'] for l in soup.select(_RESULT_LINK_CSS_SELECTOR) if self._is_link_ok(l['href'])]
        logger.debug("got %d links" % len(results))
        return results

    def _is_link_ok(self, link: str) -> bool:
        """
        Check if the link is ok, i.e. not part of the excluded ones (see the excludes variable).

        :param link: the link
        :return: False if the link should be excluded from the results
        """
        return not any([re.search(exc, link) for exc in excludes])


class StartPageGeneratorFactory(ISearcher):
    """
    Implementation of a searcher using startpage. Its usage is similar to the factory described in the
    :py:mod:`~swisstext.cmd.searching.tools.google_search` module.
    """

    def __init__(self, **kwargs):
        pass

    def search(self, query) -> StartPageGenerator:
        return StartPageGenerator(query)
