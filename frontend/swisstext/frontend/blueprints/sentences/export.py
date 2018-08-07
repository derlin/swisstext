import csv

from mongoengine import QuerySet

class CsvLine(object):
    def __init__(self):
        self._line = None

    def write(self, line):
        self._line = line

    def read(self):
        return self._line


def stream_csv(sentences: QuerySet):
    buffer = CsvLine()
    writer = csv.writer(buffer)
    # write the header line first
    writer.writerow(['id', 'text', 'url', 'dialect', 'dialect_confidence', 'dialect_nb_votes'])
    yield buffer.read()
    # then yield the sentences
    for s in sentences:
        line = [
            s.id,
            s.text,
            s.url,
            s.dialect.label,
            s.dialect.confidence,
            s.dialect.count
        ]
        writer.writerow(line)
        yield buffer.read()
