from typing import List


class PageScore:
    def __init__(self, count=0, delta_count=0, delta_date=None):
        self.count = count
        self.delta_count = delta_count
        self.delta_date = delta_date


class Sentence:
    def __init__(self, text: str, proba: float):
        self.text = text
        self.proba = proba

    def __str__(self):
        return "(<%.2f|%s>)" % (self.proba * 100, self.text)


class Page:
    def __init__(self, url, score=None, parent_url=None):
        self.url = url
        self.parent_url = parent_url
        self.blacklisted = False
        self.crawl_results = None
        self.new_sg: List[Sentence] = []
        self.sentence_count = 0
        self.sg_count = 0
        self.score: PageScore = score or PageScore()

    def is_new(self) -> bool:
        return not self.score.delta_date

    def __str__(self):
        return "(<Page %s, sg=%d/%d>)" % (self.url, self.sg_count, self.sentence_count)
