#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import re
from typing import List, Dict, Iterable

import requests
from bs4 import BeautifulSoup as Soup

# link to the search startpage
from ..interfaces import ISearcher

_SEARCH_LINK = "https://www.startpage.com/do/asearch"
# parameters for the first search query
# the only missing parameter is: query=<thing to search>
# DEFAULT_PARAMS = dict(hmb=1, cat='web', cmd='process_search', engine0='v1all', abp=1, t='air', nj=0)
_DEFAULT_PARAMS = dict(cat='web', cmd='process_search', dgf=1, hmb=1, pl="", ff="")

# regex excluding some URLs we know are not interested
excludes = [
    'www.youtube.com',
    '\.pdf$',
    '\.docx?$',
]

logger = logging.getLogger(__name__)


class StartPageGeneratorFactory(ISearcher):

    def __init__(self, **kwargs):
        pass

    def search(self, query) -> Iterable[str]:
        return StartPageGenerator(query)


class StartPageGenerator:

    def __init__(self, query):
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
        }
        self._params = dict(**_DEFAULT_PARAMS, query=query)
        self._current_results = []
        self._current_offset = 0
        self._has_next = True
        self._form: Dict = None

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

        if self._form is None:
            # first request, do a simple get to fetch page 1
            r = requests.get(_SEARCH_LINK, params=self._params, headers=self._headers)
            self._form = {}
        else:
            # not the first request, use a POST with the navigation form
            self._form['data']['startat'] = self._current_offset  # update the page
            r = requests.post(self._form['url'], data=self._form['data'], headers=self._headers)

        # get data
        soup = Soup(r.text, 'html.parser')
        self._current_results.extend(self._get_links(soup))
        self._current_offset += 10

        # get the navigation form for further queries
        forms = soup.select('#jumpsbar form')
        if len(forms) == 0:
            # not more data
            self._has_next = False
        else:
            self._form['url'] = forms[0]['action']
            form_data = [(hidden['name'], hidden['value']) for hidden in forms[0].select('input[type=hidden]')]
            self._form['data'] = dict(form_data)

    def _get_links(self, soup: Soup) -> List[str]:
        """
        For each result in the page, extract the link it is pointing to.
        :param soup: a BeautifulSoup object with the HTML page
        :return: a list of links
        """
        logger.debug("getting links...")
        results = [l['href'] for l in soup.select('li[id^=result] h3 > a') if self._is_link_ok(l['href'])]
        logger.debug("got %d links" % len(results))
        return results

    def _is_link_ok(self, link: str) -> bool:
        """
        Check if the link is ok, i.e. not part of the excluded ones (see the excludes variable).

        :param link: the link
        :return: False if the link should be excluded from the results
        """
        return not any([re.search(exc, link) for exc in excludes])
