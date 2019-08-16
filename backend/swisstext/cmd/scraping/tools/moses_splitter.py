#!/usr/bin/env python3

"""
Reimplementation of moses' split-sentences.perl in pure Python 3. The behavior is equivalent to
https://bitbucket.org/luismsgomes/mosestokenizer/src/default/src/mosestokenizer/split-sentences.perl.

Changed compared to the latest split-sentences.perl:

* no support for Chinese, Hindi and Gujarati (those if code blocks were simply ignored)
* addition of a "more" option that splits on ":;" characters
* split returns a list of sentences instead of a string
* '<P>' are not added when encountering a "closing" empty line in the input (-> all empty lines are just ignored)

.. todo::

    * The more option is interesting, but we should be careful when :; are part of an emoji, a datetime
    or an url (http://). This is somewhat easy to change, but it will also change the behavior of the
    splitter when we have consecutive ;:
    * This implementation doesn't split on ?! if followed by space+lowercase... But this is common on the web (laziness)
    * The same question applies to ... (even though this one is trickier)

"""

import os
import re
import sys

import regex
from swisstext.cmd.scraping.interfaces import ISplitter


# Perl Regex substitutions:
# * \p{IsPi} => \p{Pi} or \p{Initial_Punctuation}: any kind of opening quote.
# * \p{IsPf} => \p{Pf} or \p{Final_Punctuation}: any kind of closing quote.


class MosesSplitter(ISplitter):
    """Python implementation of Moses' split_sentences.perl"""

    def __init__(self, lang='de', prefix_file=None, more=True):
        """
        :param lang: nonbreaking_prefix file to load (available: en, de)
        :param prefix_file: path to a custom nonbreaking_prefix file
        :param more: if set, systematically split on :;
        """
        self.lang = lang
        self.more = more
        self.nb_prefixes = self.load_nb_prefixes(lang, prefix_file)

    def split(self, input_text):  # -> List[str]
        # equivalent of process_text in moses, but returns a list
        current_paragraph = ''
        splits = []
        for line in input_text.split('\n'):
            if not line or line.isspace() or (line.startswith('<') and line.endswith('>')):
                # Time to process this block; we've hit a blank or <p>
                if current_paragraph:
                    splits.extend(self._do_it_for(current_paragraph, line))
                    # don't happend '<P>' on empty lines
                    # if not len(line) or line.isspace() and current_paragraph:
                    #     splits.append('<P>')  ## If we have text followed by <P>
                    current_paragraph = ""
            else:
                current_paragraph += line + ' '

        if current_paragraph:
            # Do the leftover text.
            splits.extend(self._do_it_for(current_paragraph))

        return splits

    def _do_it_for(self, input_text, markup=''):
        # process one paragraph
        if not input_text:
            return ''
        text = self.split_paragraph(input_text, self.nb_prefixes, self.more)
        if markup.startswith('<') and markup.endswith('>'):
            return f'{text}\n{markup}'
        return text

    @classmethod
    def cleanup_spaces(cls, text):
        """Normalize spaces in a text."""
        # clean up spaces
        text = re.sub(' +', ' ', text)
        text = re.sub('\n ', '\n', text)
        text = re.sub(' \n ', '\n', text)
        return text.strip()

    @classmethod
    def split_paragraph(cls, text, nb_prefixes, more=False):  # -> List[str]
        """
        Handle on paragraph of text.
        :param text: the paragraph to split
        :param nb_prefixes: the dictionary of nonbreaking_prefix (see perl implementation/doc)
        :param more: if set, systematically split on :;
        :return: a list of sentences
        """
        # text is one paragraph, this is equivalent to the preprocess perl method.

        # clean up spaces
        text = cls.cleanup_spaces(text)

        ##### Add sentence breaks as needed #####
        if more:
            # this one is present in the python wrapper, see
            # https://bitbucket.org/luismsgomes/mosestokenizer/src/default/src/mosestokenizer/split-sentences.perl
            text = regex.sub(r'([\:;])', r'\1\n', text)
            # TODO: improvement: try to keep emojis and urls intact
            # text = regex.sub(r'([\:;])([^\)\(/-])', r'\1\n\2', text)
        # Non-period end of sentence markers (?!) followed by sentence starters.
        text = regex.sub(r'([?!]) +([\'\"\(\[\¿\¡\p{Pi}]*[\p{IsUpper}])', r'\1\n\2', text)

        # Multi-dots followed by sentence starters.
        text = regex.sub(r'(\.[\.]+) +([\'\"\(\[\¿\¡\p{Pi}]*[\p{IsUpper}])', r'\1\n\2', text)

        # Add breaks for sentences that end with some sort of punctuation
        # inside a quote or parenthetical and are followed by a possible
        # sentence starter punctuation and upper case.
        text = regex.sub(r'([?!\.][\ ]*[\'\"\)\]\p{Pf}]+) +([\'\"\(\[\¿\¡\p{Pi}]*[\ ]*[\p{IsUpper}])', r'\1\n\2', text)

        # Add breaks for sentences that end with some sort of punctuation,
        # and are followed by a sentence starter punctuation and upper case.
        text = regex.sub(r'([?!\.]) +([\'\"\(\[\¿\¡\p{Pi}]+[\ ]*[\p{IsUpper}])', r'\1\n\2', text)

        # Special punctuation cases are covered. Check all remaining periods.
        words = text.split(' ')
        text = ''
        for i in range(len(words) - 1):
            m = regex.search(r'([\p{IsAlnum}\.\-]*)([\'\"\)\]\%\p{Pf}]*)(\.+)$', words[i])
            if m is not None:
                # Check if $1 is a known honorific and $2 is empty, never break.
                prefix, starting_punct, _ = m.groups()
                if prefix and nb_prefixes.get(prefix, -1) == 1 and not starting_punct:
                    pass  # Not breaking;
                elif regex.search(r'(\.)[\p{IsUpper}\-]+(\.+)$', words[i]) is not None:
                    pass  # Not breaking - upper case acronym
                elif regex.search(r'^([ ]*[\'\"\(\[\¿\¡\p{Pi}]*[ ]*[\p{IsUpper}0-9])', words[i + 1]):
                    # The next word has a bunch of initial quotes, maybe a
                    # space, then either upper case or a number
                    if not (prefix and nb_prefixes.get(prefix, -1) == 2 and not starting_punct
                            and regex.search('^[0-9]+', words[i + 1])):
                        # We always add a return for these, unless we have a
                        # numeric non-breaker and a number start.
                        words[i] = words[i] + '\n'
            text += words[i] + ' '

        # We stopped one token from the end to allow for easy look-ahead.
        # Append it now.
        text = text + words[-1]

        # clean up spaces
        text = cls.cleanup_spaces(text)

        return text.split('\n')

    @classmethod
    def load_nb_prefixes(cls, lang='en', prefix_file=None):
        """
        Read the nonbreaking_prefixes from a file
        :param lang: the language to load
        :param prefix_file: a custom file to load (has priority over lang)
        :return: the nonbreaking_prefix dictionary, with key=prefix and value=1|2.
            1 means apply anywhere, 2 means only applies when followed by digits.
        """
        if prefix_file is None:
            this_file = os.path.realpath(__file__)
            prefix_file = this_file.replace('.py', f'_prefixes.{lang}.txt')

            if not os.path.isfile(prefix_file):
                print(
                    f'WARNING: No known abbreviations for language {lang}, attempting fall-back to English version...',
                    file=sys.stderr)
                prefix_file = prefix_file.replace(f'.{lang}.txt', '.en.txt')
        else:
            print(f'Using custom prefix file: {prefix_file}', file=sys.stderr)

        prefixes = dict()
        with open(prefix_file) as f:
            for line in f:
                line = line.strip()
                if len(line) == 0 or line.startswith('#'):
                    continue

                if line.endswith('#NUMERIC_ONLY#'):
                    prefixes[line.replace('#NUMERIC_ONLY#', '').strip()] = 2
                else:
                    prefixes[line] = 1
        return prefixes


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=argparse.FileType('r'), default='-')
    parser.add_argument('-o', '--out', type=argparse.FileType('w'), default='-')
    parser.add_argument('-l', '--lang', default='de')
    parser.add_argument('-pf', '--prefix-file', default=None)
    parser.add_argument('-m', '--more', default=False, action='store_true')

    args = parser.parse_args()
    splitter = MosesSplitter(
        lang=args.lang,
        prefix_file=args.prefix_file,
        more=args.more)

    args.out.write('\n'.join(
        splitter.split(args.input.read())
    ))
