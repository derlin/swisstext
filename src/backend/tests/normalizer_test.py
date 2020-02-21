import pytest
import random
from swisstext.cmd.scraping.tools import norm_punc

test_cases = [
    # spaces
    ('  \u200A  Lots\u2005\u2008 of\t\tspaces\u00A0\u00A0\r\n  nl   ',
     'Lots of spaces\nnl'),
    ('Zero\u200dwidth\u200d joiner',
     'Zero width joiner'),
    # numbers and symbols
    ('Numbers 100\u00A0000 1.2 1,200',
     'Numbers 100000 1.2 1200'),
    ('10\u00A0% 10% 10 %',
     '10% 10% 10%'),
    # parentheses / etc.
    ('( spaces in parentheses ) (again) (again ) ( again) and emojis :) ;=)',
     '(spaces in parentheses) (again) (again) (again) and emojis :) ;=)'),
    # quotes
    # TODO: support more ? cf https://www.cl.cam.ac.uk/~mgk25/ucs/quotes.html
    ('\u00A0«\u00A0french\u00A0»\u00A0, «french,» « french »',
     '"french", "french", " french "'),
    ("""L´apostrophe versus ‘quotes’\nx""",
     """L'apostrophe versus "quotes"\nx"""),
    ("""X ''quotation.'' “quotation” ‛quotation,’ ‘quotation’, ‘quotation’ `quotation' X""",
     """X "quotation". "quotation" "quotation", "quotation", "quotation" 'quotation' X"""),
    ("Strange ,punct,and ,  spaces .",
     "Strange, punct, and, spaces."),
    # accents: diacritics, NFD => NFC + strip weird ones
    ("e\u0302tr\u0349e ou\u0300 e\u0301tant u\u0308mlaut .\u0308 -\u030Fêùéä",
     "être où étant ümlaut. -êùéä"),
    # dashes and hyphens
    ("Sof\u00ADt h\u00ADy\u00ADp\u00ADhens.\u00AD\u00AD",
     "Soft hyphens."),
    ("\u00AF.\u2010.\u2011.\u2012.\u2013.\u2015.\u2212.\uFE58.\uFE63.\uFF0D.\u1806.",
     "-." * 11)
]


def gen_tests_shuffled():
    xys = test_cases[:]
    random.shuffle(xys)
    x, y = zip(*xys)
    return '\n'.join(x), '\n'.join(y)


@pytest.mark.parametrize(
    "raw,expected",
    test_cases
)
def test_normalizer_single(raw, expected):
    res = norm_punc.normalize_text(str(raw), fix_encoding=False, strip_emojis=False)
    assert res == str(expected)


@pytest.mark.parametrize(
    "raw,expected",
    [gen_tests_shuffled() for _ in range(10)]
)
def test_normalizer_shuffled(raw, expected):
    res = norm_punc.normalize_text(str(raw), fix_encoding=False, strip_emojis=False)
    assert res == str(expected)

