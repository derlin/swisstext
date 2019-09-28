import urllib.parse as up
from typing import Optional
import re

def _ignore(*args, **kwargs):
    return None

# ========== MAGENTO-LIKE

def strip_sid(parsed: up.ParseResult) -> up.ParseResult:
    """
    Remove the SID parameter from an url. SIDs are mostly used
    by magento to track the users and won't change the page rendered. See also
    `why-do-my-magento-urls-have-a-query-sid <https://feedarmy.com/kb/why-do-my-magento-urls-have-a-query-sid/>`_.

    :param url: the url
    :return: the url without sid
    """
    if 'sid=' in parsed.query:
        # TODO: here, the behavior of parse is inconsistant/changes the URL
        # e.g.:
        #   >>> up.parse_qsl('a=%7E_%7E%3B')
        #   [('a', '~_~;')]
        #   >>> up.urlencode([('a', '~_~;')])
        #   'a=~_~%3B'
        qs = up.parse_qsl(parsed.query)
        new_qs = up.urlencode(list(filter(lambda t: t[0] != 'sid', qs)))
        return parsed._replace(query=new_qs)
    return parsed

# ========== TWITTER


def _tw_remap(parsed, *args, **kwargs):
    return parsed._replace(netloc='twitter.com')


# or simply remove everything except users ?
# or simply remove intent/share then we only have to handle lang=
_twitter_qs_blacklist = {
    'lang',
    'src',  # e.g. src=hash or src=trend
    'ref_src', 'ref_url',  # another internal things
    'vertical',  # e.g. vertical=default or vertical=place (display thing ?) used mainly in search
    'via'  # external site where the link was found
}

_twitter_remap = {
    'search': _ignore,
    'mobile': _tw_remap,
    'www': _tw_remap,
}


def fix_twitter_url(parsed: up.ParseResult) -> Optional[up.ParseResult]:
    """
    (this method does nothing on URLs outside of the twitter.com domain).
    [Potentially] modify the twitter.com URLs by applying the following:

    - ignore sharing intents (e.g. ``/intent``, ``/share``);
    - replace http by https;
    - strip specific subdomains (e.g. ``mobile``, ``www``);
    - strip specific query parameters (e.g. ``lang``);

    :param parsed: a parsed URL
    :return: the fixed URL or None if the URL should be ignored
    """
    if 'twitter.com' not in parsed.netloc:
        return parsed

    # remove twitter.com/share and twitter.com/intent, both used for sharing
    if parsed.path.startswith('/intent') or parsed.path.startswith('/share'):
        return None

    # make it https
    if parsed.scheme != 'https':
        parsed = parsed._replace(scheme='https')

    # handle subdomains
    if '.twitter.com' in parsed.netloc:
        subdomain = parsed.netloc.replace('.twitter.com', '')
        if subdomain in _twitter_remap:
            parsed = _twitter_remap[subdomain](parsed, subdomain)
            if parsed is None:
                return None

    # strip uninteresting query parameters
    qs = up.parse_qs(parsed.query).items()
    if len(qs):
        parsed = parsed._replace(query=up.urlencode(
            {k: v for k, v in qs if k not in _twitter_qs_blacklist}
        ))
    return parsed


# ========== FACEBOOK

def _fb_remap(parsed, *args, **kwargs):
    return parsed._replace(netloc='www.facebook.com')


def _fb_handle_l(parsed, *args, **kwargs):
    qs = up.parse_qs(parsed.query)
    if 'u' in qs:
        return up.urlparse(qs['u'][0])
    return None


_facebook_remap = {
    'graph': _ignore,
    'login': _ignore,
    'ads': _ignore,

    '': _fb_remap,
    'touch': _fb_remap,
    'm': _fb_remap,
    'secure': _fb_remap,

    'l': _fb_handle_l,
}


def fix_fb_url(parsed: up.ParseResult) -> Optional[up.ParseResult]:
    """
    (this method does nothing on URLs outside of the facebook.com domain).
    [Potentially] modify the twitter.com URLs by applying the following:

    - ignore specific subdomains (e.g. ``login``, ``graph``);
    - replace http by https;
    - remap specifiy subdomains to www (e.g. languages such as ``de-de``, other such as ``m``, ``touch``);
    - extract and return the redirect URL targeted by ``l.facebook.com``;
    - strip off all query parameters (TODO)

    :param parsed: a parsed URL
    :return: the fixed URL or None if the URL should be ignored
    """
    if 'facebook.com' not in parsed.netloc:
        return parsed

    # make it https
    if parsed.scheme != 'https':
        parsed = parsed._replace(scheme='https')

    # extract subdomain
    subdomain = parsed.netloc.replace('facebook.com', '')
    if subdomain.endswith('.'): subdomain = subdomain[:-1]
    # handle subdomains
    if subdomain in _facebook_remap:
        parsed = _facebook_remap[subdomain](parsed, subdomain)
    elif re.match('[a-z]{2}-[a-z]{2}', subdomain):
        parsed = _fb_remap(parsed, subdomain)

    if parsed is None:
        return None
    
    # strip off all query parameters (TODO: really that clever ?)
    parsed = parsed._replace(query='')
    return parsed
