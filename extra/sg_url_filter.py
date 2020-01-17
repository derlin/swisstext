from typing import Optional

from swisstext.cmd.scraping.interfaces import IUrlFilter
from swisstext.cmd import link_utils
import urllib.parse as up
import re


class SgUrlFilter(IUrlFilter):
    EXCLUDED_DOMAINS = {
        # pdfs
        'epdf.pub',
        'archive.org',
        'www.researchgate.net',

        # cgi interface of dictionary / book
        'woerterbuchnetz.de',
        'reichstagsakten.de',  # old deutsch
        'www.dididoktor.de',  # old deutsch
        'www.dwds.de',
        'ahdw.saw-leipzig.de',
        'awb.saw-leipzig.de',
        'mvdok.lbmv.de',  # scans of old German books / affidavits
        'www.lindehe.de',
        'wwwmayr.in.tum.de',
        # https://wwwmayr.in.tum.de/spp1307/patterns/patterns_text-german_1024_edit_32.txt German .txt with strange encoding

        # misc
        'neon.niederlandistik.fu-berlin.de',  # netherlands

        # songs
        # 'www.karaoke-lyrics.net',
        # 'www.musixmatch.com',
        # 'greatsong.net',

        # schwäbisch
        'www.schoofseggl.de',
        'www.schwaebisch-englisch.de',
        'www.theater-in-bach.de',

        # other
        'yigg.de',  # redirects
    }

    def fix(self, url: str) -> Optional[str]:
        if '://www.schnupfspruch.ch/' in url:
            # remove the parameter saying from which page we got there
            return re.sub('[&\?]PrevPage=[\d]+', '', url)
        if '://www.literaturland.ch' in url:
            # all links are actually pointing to the same text...
            return 'http://www.literaturland.ch'
        if '://www.babyforum.ch/discussion/comment' in url:
            # all comments are actually behaving like anchors in the page
            # see for example https://www.babyforum.ch/discussion/3605/swissmom-party-2/p2
            # (comment links are on the dates on the upper right of posts)
            return None
        if '://www.fcbforum.ch' in url:
            if re.search('[&\?]p=', url) is not None:
                # we only want to crawl "main pages", e.g. page link or subforum link
                # the p= parameter is added when clicking on a post link
                return None
            # remove the viewfull
            return re.sub('[&\?]viewfull=1', '', url)

        elif any(f'://{excl}' in url for excl in self.EXCLUDED_DOMAINS):
            return None

        return url


if __name__ == '__main__':
    links = [l.strip() for l in """
    http://www.schnupfspruch.ch/sprueche_view.asp?MOVE=84&PrevPage=33
    http://www.literaturland.ch/appenzeller-anthologie/das-buch/
    http://skyandsea.blog/2018/07/17/traumstraende-die-schoensten-straende-von-portugal-und-galizien-grossartige-instagram-foto-strand-motive/?replytocom=193
    https://www.babyforum.ch/discussion/3559/ich-bin-huet-rauchfrei
    https://www.babyforum.ch/discussion/comment/28015/
    http://www.fcbforum.ch/forum/showthread.php?9533-News-und-Transfers-Fussball
    http://www.fcbforum.ch/forum/showthread.php?9533-News-und-Transfers-Fussball/page11
    http://www.fcbforum.ch/forum/showthread.php?s=3a4a96e31e37ae9ece97d59866386fa2&p=1062865
    http://www.fcbforum.ch/forum/showthread.php?30899-Cablecom-so-eine-scheisse&s=3a4a96e31e37ae9ece97d59866386fa2&p=1062920&viewfull=1
    http://yigg.de/neu?exturl=http%3A%2F%2Fwww.fcbforum.ch%2Fforum%2Fshowthread.php%3Ft%3D1873&title=Chiumiento+und+Behrami+im+Nati-Aufgebot
    http://woerterbuchnetz.de/cgi-bin/WBNetz/call_wbgui_py_from_form?sigle=DWB&mode=Volltextsuche&hitlist=&patternlist=&lemid=GN01312
    http://www.zeno.org/Wander-1867/A/Metzger
    http://web.archive.org/web/20010302135845/http://www.stillerhas.ch/texte/aare.html
    http://archive.org/web/20010302135845/http://www.stillerhas.ch/texte/aare.html
    """.split('\n')]

    url_filter = SgUrlFilter()

    for l in links:
        l = l.strip()
        if len(l):
            print('##', l)
            nl, ok = link_utils.fix_url(l)
            print('->', nl, ok)
            if ok:
                print('->', url_filter.fix(nl))

            print()
