import pytest
import pytest_check as check
from swisstext.cmd.scraping.tools import PatternSentenceFilter


@pytest.fixture
def custom_rules_filterer():
    return PatternSentenceFilter(rulespath=__file__.replace('.py', '.yaml'))


def test_rules():
    filterer = PatternSentenceFilter()
    for rule in filterer.rules:
        check.is_true(rule.self_check(), f'Rule #{rule.id}: {rule.descr}')


@pytest.mark.parametrize(
    "sentence,valid",
    [
        ('a a b b', True),
        ('a ', True),
        ('a', False),
        ('A a b b', False),
        ('aabb', False),
        ('', False)
    ]
)
def test_custom_rules(custom_rules_filterer, sentence, valid):
    assert custom_rules_filterer.is_valid(sentence) == valid
