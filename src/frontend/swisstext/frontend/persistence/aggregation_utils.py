from flask_mongoengine import Pagination


class PaginatedAggregationResults(Pagination):

    def __init__(self, page, per_page, command_cursor):
        # here, don't call super().__init__(), but define
        # the properties super needs in order to work as intended
        self.page = page
        self.per_page = per_page
        results = list(command_cursor)[0]
        self.items = results['items']
        self.total = 0 if not results['total'] else results['total'][0]['count']


def paginated_aggregation(collection, pipeline, page=1, per_page=20):
    skip = (page - 1) * per_page
    pipeline.append({'$facet': {
        'items': [{'$skip': skip}, {'$limit': per_page}],
        'total': [{'$count': 'count'}]
    }})
    results = collection.objects.aggregate(*pipeline)
    return PaginatedAggregationResults(page, per_page, results)
