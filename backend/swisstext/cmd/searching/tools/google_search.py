"""
This module let's you use the
`Google Custom Search API <https://developers.google.com/custom-search/json-api/v1/overview>`_
to retrieve URLs.


Example usages
---------------

Create a factory:

.. code-block:: python

    factory = GoogleGeneratorFactory(apikey="your apikey")

To **retrieve a list of results**, you can use the interface's ``top_results`` method:

.. code-block:: python

    # retrieve at most 13 results from a search using the interface
    results = factory.top_results(query="es isch sone seich", max_results=13)

If you want to use the iterator, it is advised to use ``itertools``, since it deals with
:py:class:`StopIteration` exceptions silently:

.. code-block:: python

    # retrieve at most 13 results from a search using the builtin python iterator
    results_iterator = factory.search(query="es isch sone seich")
    import itertools
    results = itertools.islice(results_iterator, 13) # won't throw StopIteration

Iterators are useful when you need to **process URLs in a loop**, or have a more complex stop criteria than
just the number of results. For that, you can use the builtin iterator interface:

.. code-block:: python

    # process results one by one using the builtin python iterator
    from sys import stderr
    results_iterator = factory.search(query="es isch sone seich")
    for i in range(13): # usually, here we have a while some_dynamic_condition
        try:
            url = next(results_iterator)
            print(f"Processing url: {url}")
            # ... do something more with the result ...
        except StopIteration:
            # even though Google is pretty good at retrieving billions of results,
            # you might hit the limit...
            print("Oops, no result left!", file=sys.stderr)
            break

You can also use the :py:meth:`GoogleGenerator.next` and :py:meth:`GoogleGenerator.has_next` methods
in place of the try-except, like so:

.. code-block:: python

    # process results one by one using the Google Iterator methods
    from sys import stderr
    results_iterator = factory.search(query="es isch sone seich")
    for i in range(13):
        if not results_iterator.has_next():
            print("Oops, no result left!", file=sys.stderr)
            break
        url = results_iterator.next()
        print(f"Processing url: {url}")
        # ... do something more with the result ...
"""
from ..interfaces import ISearcher

import requests
import logging
from typing import List, Set, Dict, Iterable

BASE_URL = 'https://www.googleapis.com/customsearch/v1'
"""google api URL
see https://developers.google.com/custom-search/json-api/v1/reference/cse/list#request for the json API reference"""

logger = logging.getLogger(__name__)

_links_fields = "items(link),queries(nextPage)" # we only need the links and the current page info in the results


class GoogleGeneratorFactory(ISearcher):
    """
    This factory creates a new :py:class:`GoogleGenerator` for each query.
    """

    def __init__(self, apikey: str, context='015058622601103575455:cpfpm27mio8', **kwargs):
        self.key = apikey
        """The Google Custom Search API key"""
        self.ctx = context
        """
        The context to use (see the official API reference for more info).
        The default context is usually fine: it is parameterized to search all the web.
        """

    def search(self, query) -> Iterable[str]:
        """Search for a query using the Google Custom Search API."""
        return GoogleGenerator(query, self.key, self.ctx)


class GoogleGenerator():
    """
    A new Google Generator should be created for each query. It allows for lazy loading of
    results, thus sparing API quotas.

    .. warning::

        This generator might raise an :py:class:`Exception`, for example if you reached your daily quota limit.
        In this case, the exception message should contain the error code and error message as delivered
        by the Google API.
    """
    def __init__(self, query, apikey: str, context='015058622601103575455:cpfpm27mio8'):
        self.key = apikey #: the Google API key
        self.ctx = context #: the context to use

        self.params = dict(key=self.key, cx=self.ctx, q='%s' % query, fields=_links_fields)
        self._start_offset = 1  # offset for the next query (begins at result 1)
        self._count = 10  # the API returns at most ten results, so always pull the max results possible per query

        self._current_results: List = [] # cache of the results returned by the last query
        self._has_next = True # flag to detect if we reached the last page or not
        logger.debug("Searching %s" % query)

    def __iter__(self):
        return self

    def __next__(self) -> str:
        if not self.has_next():
            raise StopIteration
        return self._current_results.pop()

    def next(self) -> str:
        """
        .. note::
            If you use this method directly (instead of the classic python iterator interface), you
            need to check that results are available by yourself using the :py:meth:`has_next` method.
        """
        return self._current_results.pop()

    def has_next(self) -> bool:
        if len(self._current_results) == 0 and self._has_next:
            self._fetch_next()
        return len(self._current_results) > 0

    def _fetch_next(self):
        if not self._has_next:
            return

        # prepare query
        self.params['start'] = self._start_offset  # set the offset
        self.params['num'] = self._count  # always set the number of results to return

        # get the results
        r = self._send_query()
        json_response = r.json()

        if not 'items' in json_response:
            self._has_next = False
        else:
            # get the results
            self._current_results.extend(self._extract_results(json_response))
            # update the counters for the next query
            self._start_offset += self._count
            self._has_next = 'queries' in json_response and 'nextPage' in json_response['queries']

    def _send_query(self) -> requests.Response:
        r = requests.get(BASE_URL, params=self.params)
        if r.status_code != 200:
            json = r.json()
            raise Exception('%s (code: %d)' % (json['error']['message'], json['error']['code']))
        return r

    def _extract_results(self, json_response: Dict) -> List:
        return [o['link'] for o in json_response['items']]
