class PageScore:
    def __init__(self, count=0, delta_count=None, delta_date=None):
        self.count = count
        self.delta_count = delta_count
        self.delta_date = delta_date


class Page:
    def __init__(self, url, score=None):
        self.url = url
        self.crawl_results = None
        self.sg = None

        self.score = score or PageScore()