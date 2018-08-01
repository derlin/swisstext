from typing import List

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, validators, SelectField, IntegerField

from swisstext.frontend.utils.search_form import SearchForm

def get_default_seeds_pipeline() -> List:
    return [
        {'$lookup':
            {
                'from': 'urls',
                'localField': '_id',
                'foreignField': 'source.extra',
                'as': 'use'
            }},
        {'$project':
            {
                'id': '$_id',
                'source': '$source',
                'count': '$count',
                'deleted': '$deleted',
                'delta_date': '$delta_date',
                'date_added': '$date_added',
                'usages': {'$size': '$search_history'},
                'urls': {'$size': '$use'}
            }}
    ]


class AddSeedForm(FlaskForm):
    seed = StringField(
        render_kw=dict(placeholder='Swiss German search term(s)'),
        validators=[validators.Length(min=3), validators.DataRequired()]
    )
    test = SubmitField('Submit')
    cancel = SubmitField('Cancel')
    add = SubmitField('I am sure, add it!')


class DeleteSeedForm(FlaskForm):
    comment = StringField(
        'Comment',
        validators=[validators.Optional(), validators.Length(max=100)],
        render_kw={'placeholder': 'optional comment'})
    delete = SubmitField('Delete seed')


class SearchSeedsForm(SearchForm):
    search = StringField(
        'Search'
    )
    min_count = IntegerField(
        'Minimum valid URLs found',
        default=0
    )

    search_history = IntegerField(
        'Minimum usage',
        default=0
    )

    show_deleted = BooleanField('Show deleted seeds as well', default=False)

    sort = SelectField(
        'Order by',
        choices=[
            ('id', 'A-Z'),
            ('date_added', 'Creation date'),
            ('delta_date', 'Last use'),
            ('count', 'New URLs found'),
            ('urls', 'Valid URLs found'),
            ('usages', 'Time used'),
        ],
        default='delta_date'
    )

    sort_order = BooleanField('Ascending', default=True)

    # def get_mongo_params(self, **kwargs) -> Dict:
    #     query_params = dict(**kwargs)
    #
    #     if not self.show_deleted.data:
    #         query_params['deleted__exists'] = False
    #
    #     if self.search.data:
    #         query_params['id__icontains'] = self.search.data.strip()
    #
    #     if self.min_count.data and self.min_count.data > 0:
    #         query_params['count__gte'] = self.min_count.data
    #
    #     if self.search_history.data:
    #         query_params['search_history__0__exists'] = self.search_history.data == 'True'
    #
    #     return query_params

    def get_search_pipeline(self):
        pipeline = get_default_seeds_pipeline()

        match = dict()
        if not self.show_deleted.data:
            match['deleted'] = {'$exists': False}

        if self.search.data:
            match['id'] = {'$regex': self.search.data.strip()}

        if self.min_count.data and self.min_count.data > 0:
            match['urls'] = {'$gte': self.min_count.data}

        if self.min_count.data and self.min_count.data > 0:
            match['usages'] = {'$gte': self.min_count.data}

        if match: pipeline.append({'$match': match})

        sort = {self.sort.data: [-1, 1][self.sort_order.data]}
        pipeline.append({'$sort': sort})

        return pipeline
