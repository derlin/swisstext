# ---------------------- jinja filters
from urllib.parse import unquote, quote


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

def register(app):
    app.jinja_env.filters['toColor'] = eanToColor
    app.jinja_env.filters['unquote'] = unquote
    app.jinja_env.filters['quote'] = quote
    app.jinja_env.filters['datetime'] = format_datetime

    # make the privileges static class available
    # app.jinja_env.globals.update(privilege=Privileges)
