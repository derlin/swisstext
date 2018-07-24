# ---------------------- jinja filters
from urllib.parse import unquote, quote

from flask import request


def eanToColor(ean, opacity=1):
    color = ""
    while len(ean) >= 2:
        n = int(ean[:2]) / 90 * 255
        color += "%02x" % int(n)
        ean = ean[2:]
    color = color[:6] + "%02x" % int(opacity * 255)
    return "#" + color


def format_datetime(d, format='%Y-%m-%d at %H:%M'):
    return d.strftime(format)


def encode_referer(endpoint, **kwargs):
    if len(kwargs):
        ref_args = ";".join("{},{}".format(*e) for e in kwargs.items())
        return dict(ref=endpoint, ref_args=ref_args)
    else:
        return dict(ref=endpoint)


def register(app):
    app.jinja_env.filters['toColor'] = eanToColor
    app.jinja_env.filters['unquote'] = unquote
    app.jinja_env.filters['quote'] = quote
    app.jinja_env.filters['datetime'] = format_datetime
    app.jinja_env.globals.update(encode_referer=encode_referer)

    # make the privileges static class available
    # app.jinja_env.globals.update(privilege=Privileges)
