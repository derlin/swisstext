# ---------------------- jinja filters
from urllib.parse import unquote, quote, urlparse, urlunparse
from swisstext.frontend.persistence.models import DialectsWrapper

def percentToColor(percent, opacity=1):
    hue = percent * 120
    return 'hsl(%d,100%%,50%%)' % hue
    # percent *= 100
    # from math import floor
    # r = 255 if percent < 50 else floor(255 - (percent * 2 - 100) * 255 / 100)
    # g = 255 if percent > 50 else floor((percent * 2) * 255 / 100)
    # return 'rgba(%d, %d, 0, %f)' % (r, g, opacity)


def format_percent(val):
    return "%.2f" % (100 * val)


def format_datetime(d, format='%Y-%m-%d %H:%M'):
    return d.strftime(format)


def encode_next_url(current_url):
    c = urlparse(current_url)
    return urlunparse(('', '', c.path, c.params, c.query, ''))


def register(app):
    app.jinja_env.filters['toColor'] = percentToColor
    app.jinja_env.filters['unquote'] = unquote
    app.jinja_env.filters['quote'] = quote
    app.jinja_env.filters['datetime'] = format_datetime
    app.jinja_env.filters['percent'] = format_percent
    app.jinja_env.globals.update(encode_next_url=encode_next_url)
    app.jinja_env.globals.update(Dialects=DialectsWrapper)

    # make the privileges static class available
    # app.jinja_env.globals.update(privilege=Privileges)
