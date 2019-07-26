import os
from swisstext.cmd.scraping.tools.pattern_sentence_filter import create_filter_using_regex_module

def LeipzigSentenceFilter(rulespath = None):
    if rulespath is None:
        rulespath = os.path.realpath(__file__)[:-2] + 'yaml'

    return create_filter_using_regex_module(rulespath=rulespath)


# if __name__ == '__main__':
#     ft = LeipzigSentenceFilter()
#     with open('/private/tmp/de.uni_leipzig.asv.tools.sentencecleaner-master/testdata/inputfile_raw') as f:
#         lines = ft.filter([l.strip() for l in f])
#         print('\n'.join(lines))
