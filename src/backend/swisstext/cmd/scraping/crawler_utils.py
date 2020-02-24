import os
import threading
import logging

logger = logging.getLogger(__name__)

#: Default user-agent if not overriden
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.89 Safari/537.36'
#: Timeout used in requests.get
GET_TIMEOUT = 60
#: Timeout used when rendering page using requests-html
RENDER_TIMEOUT = 60

# suppress warning for invalid SSL certificates
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

__all__ = ['do_get']

if os.getenv('RENDER_JS', '0').lower().strip() in ['1', 'true', 'yes', 'y']:

    try:
        import websockets

        # This is to avoid `pyppeteer.errors.NetworkError: Protocol error Target.createTarget: Target closed.`
        # See https://github.com/miyakogi/pyppeteer/issues/234#issuecomment-518215288
        wv = websockets.__version__
        if not wv.strip().startswith('6'):
            print(f'Wrong websockets version {wv}, should be v6. Please run pip install websockets==6')
            exit(1)
    except ModuleNotFoundError:
        pass

    try:
        import pyppeteer
        import asyncio

        logger.info('using REQUESTS_HTML for scraping')


        class Response:
            def __init__(self, headers, content):
                self.headers = headers
                self.text = content
                self.encoding = 'utf-8'

            @property
            def content(self):
                return self.text.encode(self.encoding)


        class JsRenderer:

            def __init__(self, loop=None, headless=True, ignoreHTTPSErrors=True, browser_args=['--no-sandbox']):
                self.loop = loop or asyncio.get_event_loop()
                self.__browser_args = dict(
                    headless=headless, dumpio=True, ignoreHTTPSErrors=ignoreHTTPSErrors, args=browser_args)

            @property
            async def _async_browser(self):
                if not hasattr(self, "_browser"):
                    self._browser = await pyppeteer.launch(**self.__browser_args)
                return self._browser

            @property
            def browser(self):
                if not hasattr(self, "_browser"):
                    self.loop = asyncio.get_event_loop()
                    if self.loop.is_running():
                        raise RuntimeError("Cannot use jsRenderer within an existing event loop.")
                    self._browser = self.loop.run_until_complete(self._async_browser)
                return self._browser

            async def _async_render(self, url, wait=0.2, timeout=60, waitUntil='networkidle0', **kwargs):
                try:
                    page = await self.browser.newPage()
                    # Wait before rendering the page, to prevent timeouts.
                    await asyncio.sleep(wait)
                    # Load the given page (GET request, obviously.)
                    response = await page.goto(url, timeout=timeout * 1000, waitUntil=waitUntil, **kwargs)
                    # Return the content of the page, JavaScript evaluated.
                    content = await page.content()
                    # Cleanup
                    await page.close()
                    page = None

                    return Response(headers=response.headers, content=content)

                except TimeoutError:
                    await page.close()
                    return None

            def render(self, url, retries=1, **kwargs):
                response = None
                for i in range(retries):
                    try:
                        response = self.loop.run_until_complete(self._async_render(url=url, **kwargs))
                        if response is not None:
                            break
                    except TypeError:
                        pass

                if not response:
                    raise Exception("Unable to render the page. Try increasing timeout")
                return response


        # This is to avoid `RuntimeError: There is no current event loop in thread 'XXX'.` when using threads.
        # See https://github.com/psf/requests-html/issues/155#issuecomment-377723137
        _RENDERER = JsRenderer()
        _ = _RENDERER.browser
        _LOCK = threading.Lock()


        def do_get(url, headers=None, timeout=RENDER_TIMEOUT):  # -> Response
            if headers is None:
                headers = dict()
            headers.setdefault('User-Agent', DEFAULT_USER_AGENT)

            try:
                while not _LOCK.acquire(timeout=60 * 2):
                   logger.debug(f'@{threading.currentThread().name} still waiting for lock after 2 minutes')
                print(f'@{threading.currentThread().name} got lock: {url}')
                resp = _RENDERER.render(url, timeout=timeout)
            finally:
                logger.debug(f'@{threading.currentThread().name} releasing lock')
                _LOCK.release()

            return resp

    except ModuleNotFoundError:
        print('Error: RENDER_JS set but pyppeteer/asyncio not found. Please, run pip install "pyppeteer>=0.0.14"')
        exit(1)

else:
    import requests

    logger.info('using REQUESTS for scraping')


    def do_get(url, headers=None, timeout=GET_TIMEOUT):  # resp
        if headers is None:
            headers = dict()
        headers.setdefault('User-Agent', DEFAULT_USER_AGENT)

        # ignore SSL certificates
        resp = requests.get(url, verify=False, stream=True, headers=headers, timeout=timeout)
        # this triggers content decoding, thus can generate ContentDecodingError
        _ = resp.content
        return resp
