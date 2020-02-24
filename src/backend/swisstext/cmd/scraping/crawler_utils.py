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
        from requests_html import HTMLSession

        logger.info('using REQUESTS_HTML for scraping')
        # This is to avoid `RuntimeError: There is no current event loop in thread 'XXX'.` when using threads.
        # See https://github.com/psf/requests-html/issues/155#issuecomment-377723137
        _SESSION = HTMLSession(browser_args=['--no-sandbox', '--headless'])
        _SESSION.browser
        _LOCK = threading.Lock()


        def do_get(url, headers=None, timeout=GET_TIMEOUT,
                   render_timeout=RENDER_TIMEOUT):  # -> Response
            if headers is None:
                headers = dict()
            headers.setdefault('User-Agent', DEFAULT_USER_AGENT)

            try:
                while not _LOCK.acquire(timeout=60 * 2):
                    logger.debug(f'@{threading.currentThread().name} still waiting for lock after 2 minutes')
                print(f'@{threading.currentThread().name} got lock: {url}')
                # ignore SSL certificates
                resp = _SESSION.get(url, verify=False, stream=True, timeout=timeout)
                # , pyppeteer_args=dict(dumpio=True)) TODO for requests_html v0.11.0 (planned for feb 26 2020)
                resp.html.render(timeout=render_timeout)
                resp._content = resp.html.raw_html
                resp.close()
            finally:
                logger.debug(f'@{threading.currentThread().name} releasing lock')
                _LOCK.release()

            return resp

    except ModuleNotFoundError:
        print('Error: RENDER_JS set but requests_html not found. Please, run pip install requests_html')
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
