import os
import threading
import logging
import datetime

import requests
import urllib3

logger = logging.getLogger(__name__)

#: Default user-agent if not overriden
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.89 Safari/537.36'
#: Timeout used in requests.get
GET_TIMEOUT = 60
#: Timeout used when rendering page using requests-html
RENDER_TIMEOUT = 60

# suppress warning for invalid SSL certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

__all__ = ['do_get']


# DEFAULT

def _requests_do_get(url, headers=None, timeout=GET_TIMEOUT):  # resp
    if headers is None:
        headers = dict()
    headers.setdefault('User-Agent', DEFAULT_USER_AGENT)

    # ignore SSL certificates
    resp = requests.get(url, verify=False, stream=True, headers=headers, timeout=timeout)
    # this triggers content decoding, thus can generate ContentDecodingError
    _ = resp.content
    return resp


if os.getenv('RENDER_JS', '0').lower().strip() in ['0', 'false', 'no', 'n', 'off']:
    logger.info('using REQUESTS for scraping')
    do_get = _requests_do_get

else:
    one_browser_per_thread = os.getenv('RENDER_JS', '0') == '2'
    logger.info('using REQUESTS_HTML for scraping')

    # == import modules

    try:
        import pyppeteer
        import asyncio
    except ModuleNotFoundError:
        print('Error: RENDER_JS set but pyppeteer not found. Please, run pip install "pyppeteer2"')
        exit(1)


    # == define utility classes

    class JsRenderer:

        def __init__(self, loop=None, headless=True, ignoreHTTPSErrors=True, browser_args=['--no-sandbox']):
            # the loop will be attached to the thread calling init
            self.loop = loop or asyncio.new_event_loop()
            self._browser_args = dict(headless=headless, ignoreHTTPSErrors=ignoreHTTPSErrors, args=browser_args)
            self.__browser = None
            self.__lock = threading.Lock()

        @property
        async def _async_browser(self):
            if self.__browser is None:
                self.__browser = await pyppeteer.launch(
                    # avoid exception "signal only works in main thread"
                    # see https://stackoverflow.com/a/54030151
                    handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False,
                    devtools=False,
                    # if not set, will freeze after ~12 requests
                    # see https://github.com/miyakogi/pyppeteer/issues/167#issuecomment-442389039
                    # note that another way to avoid too much output AND the bug is to change line 165 of
                    # pyppeteer's launcher.py:
                    #    options['stderr'] = subprocess.DEVNULL # vs subprocess.STDOUT
                    dumpio=True, logLevel='ERROR',
                    **self._browser_args)
            return self.__browser

        @property
        def browser(self):
            if not hasattr(self, "_browser"):
                self.__browser = self.loop.run_until_complete(self._async_browser)
            return self.__browser

        async def async_render(self, url, timeout=60, waitUntil='networkidle0', **kwargs):
            page, browser = None, None
            try:
                browser = await self._async_browser
                start = datetime.datetime.now()
                page = await browser.newPage()
                # Make the page a bit bigger (height especially useful for sites like twitter)
                await page.setViewport({'height': 1000, 'width': 1200})
                try:
                    # Load the given page (GET request, obviously.)
                    response = await page.goto(url, timeout=timeout * 1000, waitUntil=waitUntil, **kwargs)
                except pyppeteer.errors.TimeoutError:
                    logger.info(f'{url}: timeout error on {waitUntil}. Trying domcontentloaded...')
                    # Try again if the navigation failed, only waiting for dom this time
                    response = await page.goto(url, timeout=timeout * 1000, waitUntil='domcontentloaded', **kwargs)

                if response is None:
                    # shouldn't happen, but ... see https://github.com/miyakogi/pyppeteer/issues/299
                    return None

                # Return the content of the page, JavaScript evaluated.
                content = await page.content()
                return self._create_response(response, content, datetime.datetime.now() - start)

            except pyppeteer.errors.TimeoutError:
                logger.info(f'{url}: timeout error (final).')
                return None
            except pyppeteer.errors.NetworkError as e:
                if browser and browser.process.poll() is not None:
                    logger.warning(f'{url}: browser process is dead. Restarting')
                    # the chromium process was killed...
                    # close the browser so it is recreated on next call
                    await self.async_close()
                raise e
            finally:
                if page:  # avoid leaking pages !!
                    await page.close()

        def render(self, url, **kwargs):
            try:
                self.__lock.acquire()
                response = self.loop.run_until_complete(self.async_render(url=url, **kwargs))
                if response is None:
                    # May happen on incorrect gzip encoding ... see https://github.com/miyakogi/pyppeteer/issues/299
                    # Since I am not sure it is always the reason, back to requests which provides good
                    # exception messages, such as:
                    #    (Received response with content-encoding: gzip, but failed to decode it.',
                    #     error('Error -3 while decompressing data: incorrect header check'))
                    return _requests_do_get(url, headers=None, timeout=kwargs.get('timeout', 60))
                return response
            finally:
                self.__lock.release()

        def _create_response(self, response, content, elapsed=None, with_history=True):
            # Generate a requests.Response.
            # The only attributes not updated are: cookies, elapsed
            resp = requests.Response()
            # url and content
            resp.url = response.url
            resp._content, resp.encoding = content.encode('utf-8'), 'utf-8'
            # headers
            resp.headers.update(response.headers)
            # status
            resp.status_code = response.status
            resp.reason = requests.status_codes._codes[resp.status_code][0]
            # history
            if with_history:
                resp.history = [
                    self._create_response(req.response, "", with_history=False)  # avoid endless recursion
                    for req in response.request.redirectChain]
            # time elapsed
            resp.elapsed = elapsed if elapsed is not None else datetime.timedelta(0)
            return resp

        async def async_close(self):
            if self.__browser is not None:
                await self.__browser.close()
            self.__browser = None

        def close(self):
            try:
                self.__lock.acquire()
                self.loop.run_until_complete(self.async_close())
            finally:
                self.__lock.release()


    # == define the actual do_get

    from collections import defaultdict

    if one_browser_per_thread:
        # each thread will create its own JsRenderer instance
        _RENDERER = defaultdict(lambda: JsRenderer())
    else:
        # create one JsRenderer instance, shared by all threads
        renderer = JsRenderer()
        _RENDERER = defaultdict(lambda: renderer)


    def do_get(url, headers=None, timeout=RENDER_TIMEOUT):  # -> Response
        if headers is None:
            headers = dict()
        headers.setdefault('User-Agent', DEFAULT_USER_AGENT)
        renderer = _RENDERER[threading.current_thread().name]
        resp = renderer.render(url, timeout=timeout)

        return resp
