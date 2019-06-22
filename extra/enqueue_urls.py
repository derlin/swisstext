import argparse
import sys

from swisstext.mongo.models import MongoURL, Source, SourceType, get_connection
from urllib.parse import urlparse
import logging


def is_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url_file', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('-source_info', type=str, default=None)
    parser.add_argument('-host', type=str, default='localhost')
    parser.add_argument('-port', type=int, default=27017)
    parser.add_argument('-db', type=str, default='swisstext')
    parser.add_argument('-d', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(
        stream=sys.stderr,
        format="[%(levelname)-5s] %(message)s",
        level=logging.DEBUG if args.d else logging.INFO)

    get_connection(db=args.db, host=args.host, port=args.port)

    enqueued, malformed = 0, 0
    for i, line in enumerate(args.url_file):
        url = line.strip()
        if len(url) == 0 or url.isspace():
            continue

        if not is_url(url):
            malformed += 1
            logging.error(f'malformed url: {url}')

        elif MongoURL.exists(url):
            logging.debug(f'Duplicate url {url}. Skipping.')

        else:
            MongoURL.create(url, Source(SourceType.UNKNOWN, args.source_info)).save()
            enqueued += 1
            logging.debug(f'enqueued {url}')

    print(f'Enqueued URLs: {enqueued}/{i+1} ({malformed} malformed).')


if __name__ == '__main__':
    main()
