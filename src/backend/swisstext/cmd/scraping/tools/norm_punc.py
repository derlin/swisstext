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

__all__ = ['Normalizer', 'normalize_text']

import argparse
import re
import sys
import unicodedata

REG, STR = 0, 1  # flags for using re.sub vs string.replace

# from Leipzig rules
wrong_encoding_pattern = re.compile(r'\u0007|\u007F|\u0080-\u00A0|\u00C2|\u00C3|\u0084\uFFFD|\uF0B7|\u00AD', re.UNICODE)
# misc symbols + http://stackoverflow.com/a/13752628/6762004
emoji_pattern = re.compile('[\u2300-\u23ff\u2b50-\u2b55\u2600-\u2800\U00010000-\U0010FFFF]', re.UNICODE)

spaces_pattern = re.compile(
    # non-breakable space + https://www.compart.com/en/unicode/category/Zs
    '[\u00A0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200A\u202F\u205F\u3000 ]+',
    flags=re.UNICODE
)

normalization_patterns = [
    (t, r if t == STR else re.compile(r), s) for (t, r, s) in
    [  # largely inspired from Moses normalize-punctuation.perl (lang=de)
        # strip control chars and \t, \r, but not \n (0x0A) + \u200d (zero-width joiner)
        (REG, u'[\x00-\x09\x0B-\x1F\x7F-\x9F\u200d]', ' '),
        # strip soft-hyphen (and don't replace it by space: http://jkorpela.fi/shy.html)
        (STR, '\u00AD', ''),
        # strip extra combining diacritics (given unicodedata.normalize was run prior to this)
        (REG, '[\u0300-\u036F\uFE00-\uFE0F]', ''),
        # replace variation selectors (0xFE0F is often used, sometimes in a row...)
        (REG, '[\u0300-\u036F\uFE00-\uFE0F]', ' '),
        # strip the � character, except when it might help detect a wrong encoding issue (shouldn't happen if ftfy is installed)
        (REG, r'([^\u0084]?)\uFFFD+', r'\1'),
        # normalize unicode punctuation
        (STR, '`', "'"),
        (STR, "''", ' " '),
        (STR, '„', '"'),
        (STR, '“', '"'),
        (STR, '”', '"'),
        (STR, '—', ' - '),
        (REG, u'[\u00AF\u2010-\u2015\u2212\uFE58\uFE63\uFF0D\u1806]', '-'),  # dashes
        (STR, '´', "'"),
        (REG, r'([^\W\d_])[‘’]([^\W\d_])', r"\1'\2"),  # I
        (STR, '‘', '"'),
        (STR, '’', '"'),
        (STR, u'\u0092', "'"),
        (STR, u'\u0093', '"'),
        (STR, '‚', '"'),
        (STR, "''", '"'),
        (STR, '…', '...'),
        # French quotes
        (STR, '\u00A0«\u00A0', ' "'),
        (STR, '«\u00A0', '"'),
        (STR, '«', '"'),
        (STR, '\u00A0»\u00A0', '" '),
        (STR, '\u00A0»', '"'),
        (STR, '»', '"'),
        # other symbols
        (STR, '‹', '<'),
        (STR, '›', '>'),
        # ligatures
        (STR, 'œ', 'oe'),
        (STR, 'æ', 'ae'),
        (STR, 'ﬁ', 'fi'),
        (STR, 'ﬀ', 'ff'),
        (STR, 'ﬂ', 'fl'),
        (STR, 'ĳ', 'ij'),
        # remove pseudo-spaces in specific settings
        (STR, '\u00A0%', '%'),
        (STR, '\u00A0:', ':'),
        (STR, '\u00A0?', '?'),
        (STR, '\u00A0!', '!'),
        (STR, '\u00A0;', ';'),
        # ensure , is not left alone
        (STR, ' ,', ','),
        (STR, ',', ', '),
        # German/Spanish/French "quotation", followed by comma, style
        (STR, ',"', '",'),
        (REG, r'(\.+)"(\s*[^<])', r'"\1\2'),  # don't fix period at end of sentence
        (REG, r'(\d)\u00A0(\d)', r'\1,\2'),
        # normalize space
        (REG, spaces_pattern, ' '),
        # normalize spaces
        (REG, '(\d) \%', r'\1%'),
        # the following is a very bad idea because of emojis
        # (STR, '(', ' ('),
        # (STR, ')', ') '),
        # (REG, r'\) +([\.\!\:\?\;\,])', r')\1'),
        # (STR, '( ', '('),
        # (STR, ' )', ')'),
        # (STR, ' :', ':'),
        # (STR, ' ;', ';'),
        # normalize spaces around, trying to avoid emojis
        (REG, r'([\w"\']) ?(:|;) ?([\w"\'\n]|$)', r'\1\2 \3'),
        (STR, ' , ', ', '),
        (STR, ' .', '.'),  # TODO: useful ?
        (REG, '\( +(\w|\d)', r'(\1'),
        (REG, '(\w|\d) +\)', r'\1)'),
    ]]


def normalize_text(text, fix_encoding=False, strip_emojis=False):
    """
    Normalize text:

    * normalize accents (using NFC convention),
    * strip control/invisible chars and leftover combining diacritics,
    * undo ligatures,
    * normalize quotes, apostrophes and unicode characters (dashes, etc.),
    * normalize spaces (all spaces, including nbsp and tabs, will be encoded as 0x20),
    * strip and collapse multiple spaces into one,
    * etc.

    Optionally:

    * try to detect and fix encoding issues (see `ftfy.fix_encoding <https://ftfy.readthedocs.io/en/latest/>`_)
       on a per-sentence basis (delimited by newlines);
    * strip emojis (using a simple regex, not all cases are covered !)


    :param text: the text to normalize, newlines will be preserved;
    :param fix_encoding: if set, use ftfy to fix encoding issues on a per-sentence basis;
    :param strip_emojis: if set, try to find and strip unicode emojis;
    :return: the normalized text
    """
    # optionally fix encoding using ftfy
    if fix_encoding and wrong_encoding_pattern.search(text) is not None:
        try:
            import ftfy
            text = '\n'.join(
                ftfy.fix_encoding(t) if wrong_encoding_pattern.search(t) is not None else t
                for t in text.split('\n')
            )
        except ModuleNotFoundError:
            print('WARNING: norm_punc.py, fixing encoding requires the ftfy package: pip install ftfy.')

    # normalize (e.g. combining diacritics)
    text = unicodedata.normalize('NFC', text)

    # optionally strip emojis
    if strip_emojis:
        # I formally used the emoji library, which is really nice but slooooow (and doesn't cover ASCII misc symbols).
        # I thus preferred to use a simpler regex that covers most cases is is waaaay faster
        # (203ms to process 164343 short sentences, against 31s with emoji)
        text = emoji_pattern.sub(' ', text)

    # apply patterns in order
    for i, (typ, pattern, replace) in enumerate(normalization_patterns):
        if typ == REG:
            text = pattern.sub(replace, text)
        else:
            text = text.replace(pattern, replace)

    # normalize spaces
    text = spaces_pattern.sub(' ', text)

    # don't forget to normalise spaces in the beginning and end
    text = re.sub(r'(^|\n)\s+', r'\1', text)
    text = re.sub(r'\s+(\n|$)', r'\1', text)

    return text


class Normalizer():
    """A wrapper around :py:meth:`normalize_text`"""

    def __init__(self, **kwargs):
        """Initialize a normalizer. The ``kwargs`` will be passed to :py:meth:`normalize_text` as-is. """
        self.kwargs = kwargs  #: extra options to pass to :py:meth:`normalize_text`

    def normalize(self, text):
        """Call :py:meth:`normalize_text` on ``text`` with the extra :py:attr:`kwargs` options."""
        return normalize_text(text, **self.kwargs)


# ---

def cli():
    parser = argparse.ArgumentParser(
        description=
        "Normalise text (remove control chars, uncurl quotes, normalise spaces...)"
    )
    parser.add_argument('-i', type=argparse.FileType('r'), required=True)
    parser.add_argument('-fe', '--fix-encoding', default=False, action='store_true')
    parser.add_argument('-se', '--strip-emojis', default=False, action='store_true')
    parser.add_argument('-o', '--out', type=argparse.FileType('w'), default=sys.stdout)
    args = parser.parse_args()

    try:
        text = normalize_text(args.i.read(), fix_encoding=args.fix_encoding, strip_emojis=args.strip_emojis)
        args.out.write(text)
    except ModuleNotFoundError as e:
        print(e)
        exit(1)


if __name__ == '__main__':
    cli()
