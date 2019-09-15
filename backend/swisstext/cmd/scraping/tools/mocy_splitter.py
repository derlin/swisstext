#!/usr/bin/env python3

"""
This splitter implementation was heavily inspired from moses' split-sentences.perl. It requires only basic python 3 modules
and the `regex <https://pypi.org/project/regex/>`_ module (which supports unicode regexes).

Main changes compared to the latest split-sentences.perl:

* implemented with Swiss-German (Web) in mind: no support for Chinese, Hindi and Gujarati,
  numbers and quotes conventions based on this language only;
* addition of a "more" option that splits on ":;" characters (but tries to keep emojis and URLs intact);
* lowercase letters can also be signals of start-of-sentence (often seen on the web);
* more aggressive splits on ``?!`` characters;
* split returns a list of sentences instead of a string;
* it is possible to load multiple nonbreaking prefix lists (merged into one lookup table);
* no support for <p> tags (I didn't get the purpose of this option anyway)

"""

import os
import re
import sys

import regex
from swisstext.cmd.scraping.interfaces import ISplitter

import logging

logger = logging.getLogger(__name__)

# Non-breaking prefix entries
_UNDEF = -1  #: the prefix doesn't exist
_ANY = 1  #: the prefix always applies
_NUMERIC_ONLY = 2  #: the prefix applies only when followed by number(s)


# Perl Regex substitutions:
# * \p{IsPi} => \p{Pi} or \p{Initial_Punctuation}: any kind of opening quote.
# * \p{IsPf} => \p{Pf} or \p{Final_Punctuation}: any kind of closing quote.


class MocySplitter(ISplitter):
    """
    A splitter largely inspired from Moses' split_sentences.perl. The name is a contraction of Moses and Lucy.
    Most important changes:

    * a start of sentence doesn't need to be an uppercase, lowercase letters will do too;
    * the more parameter let you choose to break on ';:' as well;
    * end of sentences '?!' are better handled
    * multiple nonbreaking_prefix files can be used at once (rules will be merged)

    """

    def __init__(self, langs=None, prefix_file=None, more=True):
        """
        :param lang: a List[str] of language(s) for nonbreaking_prefix file to load (default: en, de)
        :param prefix_file: path to a custom nonbreaking_prefix file
        :param more: if set, systematically split on ``:;``
        """
        self.langs = langs if langs is not None else ['en', 'de']  #: nonbreaking prefixes files to load
        self.more = more  #: whether or not to split on ``:;``
        self.nb_prefixes = self.load_nb_prefixes(self.langs, prefix_file)  #: nonbreaking prefix lookup table

    def split(self, input_text):  # -> List[str]
        """
        Split a text into sentences. Newlines already present in text will be preserved.

        :param input_text: the input text
        :return: a list of sentences (no blanks)
        """
        # equivalent of process_text in moses, but returns a list
        current_paragraph = ''
        splits = []
        for line in input_text.split('\n'):
            if not line or line.isspace():
                # Time to process this block; we've hit a blank or <p>
                if current_paragraph:
                    splits.extend(self.split_paragraph(current_paragraph, self.nb_prefixes, self.more))
                    current_paragraph = ""
            else:
                current_paragraph += line + ' '

        if current_paragraph:
            # Do the leftover text.
            splits.extend(self.split_paragraph(current_paragraph, self.nb_prefixes, self.more))

        return splits

    @classmethod
    def cleanup_spaces(cls, text):  # -> str
        """Normalize spaces in a text."""
        # clean up spaces
        text = re.sub(' +', ' ', text)
        text = re.sub('\n ', '\n', text)
        text = re.sub(' \n ', '\n', text)
        return text.strip()

    @classmethod
    def split_paragraph(cls, text, nb_prefixes, more=False):  # -> List[str]
        """
        Handle one paragraph of text.

        :param text: the paragraph to split
        :param nb_prefixes: the dictionary of nonbreaking_prefix (see perl implementation/doc)
        :param more: if set, systematically split on :;
        :return: a list of sentences
        """
        # text is one paragraph, this is equivalent to the preprocess perl method.
        if not text:
            return ''
        # clean up spaces
        text = cls.cleanup_spaces(text)

        ##### Add sentence breaks as needed #####
        if more:
            # this one is present in the python wrapper, see
            # https://bitbucket.org/luismsgomes/mosestokenizer/src/default/src/mosestokenizer/split-sentences.perl
            # text = regex.sub(r'([\:;])', r'\1\n', text)
            # TODO: improvement: try to keep emojis, numers like 1:1 and urls intact
            text = regex.sub(r'([\:;])([^\d\)\(/-])', r'\1\n\2', text)

        # split if ?! is followed by a lowercase (often on the web)
        text = regex.sub(r'([\?!]+)([^\?!\p{Pe}\p{Pf}\"])', r'\1\n\2', text)
        # text = regex.sub(r'([?!]) +([\'\"\(\[\¿\¡\p{Pi}]*[\p{L}])', r'\1\n\2', text)

        # Multi-dots followed by sentence starters.
        text = regex.sub(r'(\.[\.]+) +([\'\"\(\[\¿\¡\p{Pi}]*[\p{L}])', r'\1\n\2', text)

        # Add breaks for sentences that end with some sort of punctuation
        # inside a quote or parenthetical and are followed by a possible
        # sentence starter punctuation and ~upper case~ letter
        text = regex.sub(r'([?!\.][\ ]*[\'\"\)\]\p{Pf}]+) +([\'\"\(\[\¿\¡\p{Pi}]*[\ ]*[\p{Lu}])', r'\1\n\2', text)

        # Add breaks for sentences that end with some sort of punctuation,
        # and are followed by a sentence starter punctuation and upper case letter.
        text = regex.sub(r'([?!\.]) +([\'\"\(\[\¿\¡\p{Pi}]+[\ ]*[\p{L}])', r'\1\n\2', text)

        # Special punctuation cases are covered. Check all remaining periods.
        words = text.split(' ')
        text = ''
        for i in range(len(words) - 1):
            # TODO: add the # as a possible sentence start ? (twitter and hashtags)
            m = regex.search(r'([\p{IsAlnum}\.\-]*)([\'\"\)\]\%\p{Pf}]*)(\.+)$', words[i])
            if m is not None:
                # Check if $1 is a known honorific and $2 is empty, never break.
                prefix, starting_punct, _ = m.groups()
                if prefix and nb_prefixes.get(prefix, _UNDEF) == _ANY and not starting_punct:
                    pass  # Not breaking prefix
                elif regex.search(r'(\.)[\p{IsUpper}\-]+(\.+)$', words[i]) is not None:
                    pass  # Not breaking - upper case acronym
                elif regex.search(r'^([ ]*[\'\"\(\[\¿\¡\p{Pi}]*[ ]*[\p{L}0-9])', words[i + 1]):
                    # The next word has maybe a bunch of initial quotes, maybe a
                    # space, then either ~upper case~ letter or a number
                    if prefix and nb_prefixes.get(prefix, _UNDEF) == _NUMERIC_ONLY and not starting_punct \
                            and regex.search('^[0-9]+', words[i + 1]):
                        # exception: we have a numeric-only prefix followed by a number
                        pass
                    else:
                        # In any other case, split
                        words[i] = words[i] + '\n'
            text += words[i] + ' '

        # We stopped one token from the end to allow for easy look-ahead.
        # Append it now.
        text = text + words[-1]

        # clean up spaces
        text = cls.cleanup_spaces(text)

        return text.split('\n')

    @classmethod
    def load_nb_prefixes(cls, langs, prefix_file=None):  # -> Dict
        """
        Read the nonbreaking_prefixes from a file or from an array of languages.

        :param langs: the language(s) to load
        :param prefix_file: a custom file to load (has priority over lang)
        :return: the nonbreaking_prefix dictionary, with key=prefix and value=1|2.
                1 means apply anywhere, 2 means only applies when followed by digits.
        """
        if prefix_file is not None:
            print(f'Using custom prefix file: {prefix_file}', file=sys.stderr)
            return cls._read_prefix_file(prefix_file)

        this_dir = os.path.dirname(os.path.realpath(__file__))
        prefix_file_pattern = os.path.join(this_dir, 'moses_splitter_prefixes.{}.txt')

        prefixes = dict()
        for lang in langs:
            prefix_file = prefix_file_pattern.format(lang)
            if not os.path.isfile(prefix_file):
                logger.warning(f'No known abbreviations for language {lang}, skipping...')
                continue
            prefixes.update(**cls._read_prefix_file(prefix_file))
            logger.info(f'Loaded prefix file for lang={lang} (prefix size: {len(prefixes)}).')
        return prefixes

    @staticmethod
    def _read_prefix_file(filename):  # -> Dict
        # load a nonbreaking_prefix lookup table from a file
        prefixes = dict()
        with open(filename) as f:
            for line in f:
                line = line.strip()
                if len(line) == 0 or line.startswith('#'):
                    continue
                if line.endswith('#NUMERIC_ONLY#'):
                    prefixes[line.replace('#NUMERIC_ONLY#', '').strip()] = _NUMERIC_ONLY
                else:
                    prefixes[line] = _ANY
        return prefixes


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=argparse.FileType('r'), default='-')
    parser.add_argument('-o', '--out', type=argparse.FileType('w'), default='-')
    parser.add_argument('-l', '--lang', action='append')
    parser.add_argument('-pf', '--prefix-file', default=None)
    parser.add_argument('-m', '--more', default=False, action='store_true')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)s: %(msg)s')

    splitter = MocySplitter(
        langs=args.lang,
        prefix_file=args.prefix_file,
        more=args.more)

    args.out.write('\n'.join(
        splitter.split(args.input.read())
    ))
