
from typing import Iterable, Generator
from urllib.parse import urljoin, urlparse, ParseResult
EXCLUDED_EXTENSIONS = dict((s, True) for s in [
    "3dv", "3g2", "3gp", "pi1", "pi2", "pi3", "ai", "amf", "amv", "art", "art", "ase", "asf", "avi", "awg", "blp",
    "bmp", "bw", "bw", "cd5", "cdr", "cgm", "cit", "cmx", "cpt", "cr2", "cur", "cut", "dds", "dib", "djvu", "doc",
    "docx", "drc", "dxf", "e2d", "ecw", "egt", "egt", "emf", "eps", "exif", "f4a", "f4b", "f4p", "f4v", "flv", "flv",
    "flv", "fs", "gbr", "gif", "gif", "gifv", "gpl", "grf", "hdp", "icns", "ico", "iff", "iff", "int", "int", "inta",
    "jfif", "jng", "jp2", "jpeg", "jpg", "jps", "jxr", "lbm", "lbm", "liff", "m2v", "m4p", "m4v", "m4v", "max", "miff",
    "mkv", "mng", "mng", "mov", "mp2", "mp4", "mpe", "mpeg", "mpeg", "mpg", "mpg", "mpv", "msp", "mxf", "nitf", "nrrd",
    "nsv", "odg", "ogg", "ogv", "ota", "pam", "pbm", "pc1", "pc2", "pc3", "pcf", "pct", "pcx", "pcx", "pdd", "pdf",
    "pdn", "pgf", "pgm", "pict", "png", "pnm", "pns", "ppm", "ppt", "pptx", "psb", "psd", "psp", "px", "pxm", "pxr",
    "qfx", "qt", "ras", "raw", "rgb", "rgb", "rgba", "rle", "rm", "rmvb", "roq", "sct", "sgi", "sgi", "sid", "stl",
    "sun", "svg", "svi", "sxd", "tga", "tga", "tif", "tiff", "v2d", "vnd", "vob", "vrml", "vtf", "wdp", "webm", "webp",
    "wmf", "wmv", "x3d", "xar", "xbm", "xcf", "xls", "xlsx", "xpm", "yuv"
])
# TODO: also exclude wikipedia pages ?

EXCLUDED_TLDS = dict((s[1:], True) for s in [
    ".af", ".ax", ".al", ".dz", ".as", ".ad", ".ao", ".ai", ".aq", ".ag", ".ar", ".am", ".aw", ".ac", ".au", ".at",
    ".az", ".bs", ".bh", ".bd", ".bb", ".eus", ".by", ".be", ".bz", ".bj", ".bm", ".bt", ".bo", ".bq", ".an", ".nl",
    ".ba", ".bw", ".bv", ".br", ".io", ".vg", ".bn", ".bg", ".bf", ".mm", ".bi", ".kh", ".cm", ".ca", ".cv", ".cat",
    ".ky", ".cf", ".td", ".cl", ".cn", ".cx", ".cc", ".co", ".km", ".cd", ".cg", ".ck", ".cr", ".ci", ".hr", ".cu",
    ".cw", ".cy", ".cz", ".dk", ".dj", ".dm", ".do", ".tl", ".tp", ".ec", ".eg", ".sv", ".gq", ".er", ".ee", ".et",
    ".eu", ".fk", ".fo", ".fm", ".fj", ".fi", ".fr", ".gf", ".pf", ".tf", ".ga", ".gal", ".gm", ".ps", ".ge", ".de",
    ".gh", ".gi", ".gr", ".gl", ".gd", ".gp", ".gu", ".gt", ".gg", ".gn", ".gw", ".gy", ".ht", ".hm", ".hn", ".hk",
    ".hu", ".is", ".in", ".id", ".ir", ".iq", ".ie", ".im", ".il", ".it", ".jm", ".jp", ".je", ".jo", ".kz", ".ke",
    ".ki", ".kw", ".kg", ".la", ".lv", ".lb", ".ls", ".lr", ".ly", ".li", ".lt", ".lu", ".mo", ".mk", ".mg", ".mw",
    ".my", ".mv", ".ml", ".mt", ".mh", ".mq", ".mr", ".mu", ".yt", ".mx", ".md", ".mc", ".mn", ".me", ".ms", ".ma",
    ".mz", ".mm", ".na", ".nr", ".np", ".nl", ".nc", ".nz", ".ni", ".ne", ".ng", ".nu", ".nf", ".nc", ".tr", ".kp",
    ".mp", ".no", ".om", ".pk", ".pw", ".ps", ".pa", ".pg", ".py", ".pe", ".ph", ".pn", ".pl", ".pt", ".pr", ".qa",
    ".ro", ".ru", ".rw", ".re", ".bq", ".an", ".bl", ".gp", ".fr", ".sh", ".kn", ".lc", ".mf", ".gp", ".fr", ".pm",
    ".vc", ".ws", ".sm", ".st", ".sa", ".sn", ".rs", ".sc", ".sl", ".sg", ".bq", ".an", ".nl", ".sx", ".an", ".sk",
    ".si", ".sb", ".so", ".so", ".za", ".gs", ".kr", ".ss", ".es", ".lk", ".sd", ".sr", ".sj", ".sz", ".se", ".ch",
    ".sy", ".tw", ".tj", ".tz", ".th", ".tg", ".tk", ".to", ".tt", ".tn", ".tr", ".tm", ".tc", ".tv", ".ug", ".ua",
    ".ae", ".uk", ".us", ".vi", ".uy", ".uz", ".vu", ".va", ".ve", ".vn", ".wf", ".eh", ".ma", ".ye", ".zm", ".zw"
] if s not in ['.ch', '.de', '.it', '.fr', '.eu', '.uk', '.us'])  # TODO: tune a bit the whitelist ?

#: Quick lookup dictionary to exclude any URL from wikipedia, except the ones from the given subdomains.
#: See `<https://en.wikipedia.org/wiki/List_of_Wikipedias>`_ for a full list of wikipedia subdomains.
INCLUDED_WIKI_DOMAINS = dict((s, True) for s in [
    "als"
])


def filter_links(base_url: str, links: Iterable[str]) -> Generator[str, None, None]:

    seen = {base_url, base_url + '/'}  # keep a set of seen urls

    for link in links:
        abs_url: str = urljoin(base_url, link)
        parsed: ParseResult = urlparse(abs_url)

        if _should_url_be_kept(parsed):
            if parsed.fragment:
                abs_url = abs_url.replace(f"#{parsed.fragment}", '')
            if abs_url not in seen:
                yield abs_url
                # add it as is
                seen.add(abs_url)
                # avoid duplicate links with just an ending slash that differ
                seen.add(abs_url[:-1] if abs_url.endswith('/') else abs_url + '/')
            else:
                pass


def _should_url_be_kept(parsed: ParseResult) -> bool:
    if not parsed.scheme or not parsed.scheme.startswith('http'):
        # not a HTTP or HTTPS URL
        return False
    if '.' in parsed.path and parsed.path.split(".")[-1].lower() in EXCLUDED_EXTENSIONS:
        # contains an unwanted extension
        return False
    if parsed.netloc.split(".")[-1].lower() in EXCLUDED_TLDS:
        # is from an unwanted tld
        return False
    if parsed.netloc.endswith("wikipedia.org") and parsed.netloc.split(".")[0].lower() not in INCLUDED_WIKI_DOMAINS:
        # is from wikipedia and not from a wanted wiki subdomain
        return False
    return True
