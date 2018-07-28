class Seed:
    def __init__(self, query: str):
        self.query = query
        self.new_links = []


    def __repr__(self):
        return "<Seed |%s| (new_links=%d)>" % (self.query, len(self.new_links))