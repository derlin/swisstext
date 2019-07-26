#!/usr/bin/env python3

#
# A python script that mimics what Moses remove-non-printing-char.perl
# and normalize-punctuation.perl do, with some slight improvements:
#  - normalize combining diacritics at the beginning (and remove any extra one, e.g. Gguppò̃ò̃s -> Gguppòòs)
#  - properly handle GSW apostrophes (i.e. ' surrounded by accented/special chars)
#  - replace [non-breakable spaces+space separator unicode category]
#    by regular spaces as a last step
#
# Lucy Linder, June 2019
#

import argparse
import re
import sys
import unicodedata

REG, STR = 0, 1  # flags for using re.sub vs string.replace

normalization_patterns = [  # largely inspired from Moses normalize-punctuation.perl (lang=de)
    # strip control chars
    (REG, u'[\x00-\x1F\x7F-\x9F]', ' '), #(STR, '\r', ""),
    # strip extra combining diacritics
    (REG, '[\u0300-\u036F]', ''),
    # remove extra spaces
    (STR, '(', ' ('),
    (STR, ')', ') '),
    (REG, r'\) +([\.\!\:\?\;\,])', r')\1'),
    (STR, '( ', '('),
    (STR, ' )', ')'),
    (REG, '(\d) \%', r'\1%'),
    (STR, ' :', ':'),
    (STR, ' ;', ';'),
    # normalize unicode punctuation
    (STR, '`', "'"),
    (STR, "''", ' " '),
    (STR, '„', '"'),
    (STR, '“', '"'),
    (STR, '”', '"'),
    (STR, '—', ' - '),
    (STR, '\u00AD', ''),  # remove soft hyphen
    (REG, u'[\u00AF\u2010-\u2015\u2212\uFE58-\uFF0D]', '-'),  # dashes
    (STR, '´', "'"),
    (REG, r'([^\W\d_])[‘’]([^\W\d_])', r"\1'\2"),  # I
    (STR, '‘', '"'),
    (STR, '’', '"'),
    (STR, '’', '"'),
    (STR, u'\u0092', "'"),
    (STR, u'\u0093', '"'),
    (STR, '‚', '"'),
    (STR, "''", '"'),
    (STR, '´´', '"'),
    (STR, '…', '...'),
    # French quotes
    (STR, ' « ', ' "'),
    (STR, '« ', '"'),
    (STR, '«', '"'),
    (STR, ' » ', '" '),
    (STR, ' »', '"'),
    (STR, '»', '"'),
    # other symbols
    (STR, '‹', '>'),
    (STR, '›', '>'),
    # ligatures
    (STR, 'œ', 'oe'),
    (STR, 'æ', 'ae'),
    # handle pseudo-spaces
    (STR, ' %', '%'),
    (STR, 'nº ', 'nº '),
    (STR, ' :', ':'),
    (STR, ' ºC', ' ºC'),
    (STR, ' cm', ' cm'),
    (STR, ' ?', '?'),
    (STR, ' !', '!'),
    (STR, ' ;', ';'),
    (STR, ', ', ', '),
    # German/Spanish/French "quotation", followed by comma, style
    (STR, ',"', '",'),
    (REG, r'(\.+)"(\s*[^<])', r'"\1\2'),  # don't fix period at end of sentence
    (REG, r'(\d) (\d)', r'\1,\2'),
]

spaces_pattern = re.compile(
    # non-breakable space + https://www.compart.com/en/unicode/category/Zs
    '[\u00A0\u0020\u00A0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200A\u202F\u205F\u3000 ]+',
    flags=re.UNICODE
)


def normalize_text(text, strip_emojis=True, fix_encoding=False):
    # normalize (e.g. combining diacritics)
    text = unicodedata.normalize('NFC', text)

    # optionally fix encoding using ftfy
    if fix_encoding:
        try:
            import ftfy
            text = ftfy.fix_encoding(text)
        except ModuleNotFoundError:
            raise ModuleNotFoundError('Fixing encoding requires the ftfy package: pip install ftfy.')

    # apply patterns in order
    for i, (typ, pattern, replace) in enumerate(normalization_patterns):
        if typ == REG:
            text = re.sub(pattern, replace, text)
        else:
            text = text.replace(pattern, replace)

    # optionally strip emojis
    if strip_emojis:
        try:
            import emoji
            text = emoji.get_emoji_regexp().sub('', text)
        except ModuleNotFoundError:
            raise ModuleNotFoundError('Stripping emojis requires the emoji package: pip install emoji.')

    # don't forget to normalise spaces in the end
    return spaces_pattern.sub(' ', text).strip()


class Normalizer():
    def normalize(self, *args, **kwargs):
        return normalize_text(*args, **kwargs)


__all__ = ['Normalizer', 'normalize_text']


# ---

def cli():
    parser = argparse.ArgumentParser(
        description=
        "Normalise text (remove control chars, uncurl quotes, normalise spaces...)"
    )
    parser.add_argument('-i', type=argparse.FileType('r'), required=True)
    parser.add_argument('--fix-encoding', default=False, action='store_true')
    parser.add_argument('--strip-emojis', default=False, action='store_true')
    parser.add_argument('-o', '--out', type=argparse.FileType('w'), default=sys.stdout)
    args = parser.parse_args()

    try:
        text = normalize_text(args.i.read(), strip_emojis=args.strip_emojis, fix_encoding=args.fix_encoding)
        args.out.write(text)
    except ModuleNotFoundError as e:
        print(e)
        exit(1)


if __name__ == '__main__':
    cli()
