#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from swisstext.searching.interfaces import ISearcher

import requests
import logging
from typing import List, Set, Dict, Iterable

# google api URL
# see https://developers.google.com/custom-search/json-api/v1/reference/cse/list#request
# for the json API reference
BASE_URL = 'https://www.googleapis.com/customsearch/v1'

logger = logging.getLogger(__name__)

_links_fields = "items(link),queries(nextPage)"


class GoogleGeneratorFactory(ISearcher):

    def __init__(self, apikey: str, context='015058622601103575455:cpfpm27mio8', **kwargs):
        self.key = apikey
        self.ctx = context

    def search(self, query) -> Iterable[str]:
        return GoogleGenerator(query, self.key, self.ctx)


class GoogleGenerator():

    def __init__(self, query, apikey: str, context='015058622601103575455:cpfpm27mio8'):
        self.key = apikey
        self.ctx = context

        self.params = dict(key=self.key, cx=self.ctx, q='"%s"' % query, fields=_links_fields)
        self.start_offset = 1  # begin at result 1
        self.count = 10  # the API returns at most ten results

        self._current_results: List = []
        self._has_next = True
        logger.debug("Searching %s" % query)

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

        # prepare query
        self.params['start'] = self.start_offset  # set the offset
        self.params['num'] = self.count  # always set the number of results to return

        # get the results
        r = self._send_query()
        json_response = r.json()

        if not 'items' in json_response:
            self._has_next = False
        else:
            # get the results
            self._current_results.extend(self._extract_results(json_response))
            # update the counters for the next query
            self.start_offset += self.count
            self._has_next = 'queries' in json_response and 'nextPage' in json_response['queries']

    def _send_query(self) -> requests.Response:
        r = requests.get(BASE_URL, params=self.params)
        if r.status_code != 200:
            json = r.json()
            raise Exception('%s (code: %d)' % (json['message'], json['code']))
        return r

    def _extract_results(self, json_response: Dict) -> List:
        return [o['link'] for o in json_response['items']]
