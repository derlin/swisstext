import pytest
from swisstext.cmd.scraping.tools import MocySplitter


@pytest.fixture
def splitter():
    return MocySplitter(keep_newlines=True, more=True, langs=['en'])


@pytest.mark.parametrize(
    "sentence,split",
    [
        # general
        ('This is a sentence\nAnd another. really ?really? True. ',
         ['This is a sentence', 'And another.', 'really ?', 'really?', 'True.']),
        # keep numbers and urls [and some emojis]
        ('1.12$. https://example.com: another website',
         ['1.12$.', 'https://example.com:', 'another website']),
        ('Hello ;-)', ['Hello ;-)']),
        ('Chapter 1:1', ['Chapter 1:1']),
        # quotes
        ('"I love this !" and "xx." are famous quote! yeah...',
         ['"I love this !" and "xx." are famous quote!', 'yeah...']),
        ('"I love this !" And "xx."! yeah...',
         ['"I love this !"', 'And "xx."!', 'yeah...']),
        # prefixes
        ('Mr. Hans, i.e. Charles, is born Jan. 16th', ['Mr. Hans, i.e. Charles, is born Jan. 16th']),
        ('Article No. 14 or No. xx.', ['Article No. 14 or No.', 'xx.']),
        # keep repeating punctuation
        ('YEAH!!! SO GREAT !!! so ??!? .',
         ['YEAH!!!', 'SO GREAT !!!', 'so ??!?', '.'])
    ]
)
def test_custom_rules(splitter, sentence, split):
    assert splitter.split(sentence) == split


def test_more_setting(splitter):
    sentence = "The test: split or not on semi-colon."
    splitter.more = False
    assert len(splitter.split(sentence)) == 1
    splitter.more = True
    assert len(splitter.split(sentence)) == 2


def test_newline_setting(splitter):
    sentence = "The test is \nsplit or not on semi-colon. Or not."
    splitter.keep_newlines = False
    assert len(splitter.split(sentence)) == 2
    splitter.keep_newlines = True
    assert len(splitter.split(sentence)) == 3
