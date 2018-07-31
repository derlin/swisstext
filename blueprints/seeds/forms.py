from typing import Dict

from flask import Blueprint
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, validators, SelectField, HiddenField, IntegerField

from utils.search_form import SearchForm

blueprint_seeds = Blueprint('seeds', __name__, template_folder='.')


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
        'Min URLs',
        default=0
    )

    search_history = SelectField(
        'Usage',
        choices=[('', 'any'), ('False', 'Never used'), ('True', 'Used at least once')],
        default=''
    )
    sort = SelectField(
        'Order by',
        choices=[('id', 'A-Z'), ('count', 'Num URLs'), ('date_added', 'Creation date')],
        default='delta_date'
    )

    sort_order = BooleanField('Ascending', default=True)

    def get_mongo_params(self, **kwargs) -> Dict:
        query_params = dict(**kwargs)

        if self.search.data:
            query_params['id__icontains'] = self.search.data.strip()

        if self.min_count.data and self.min_count.data > 0:
            query_params['count__gte'] = self.min_count.data

        if self.search_history.data:
            query_params['search_history__0__exists'] = self.search_history.data == 'True'

        return query_params

    def get_aggregation_pipeline(self):
        pipeline = [
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
                    'usages': {'$size': '$search_history'},
                    'urls': {'$size': '$use'}
                }}
        ]

        match = dict()
        if self.search.data:
            match['id'] = {'$regex': self.search.data.strip()}

        if self.min_count.data and self.min_count.data > 0:
            match['urls'] = {'$gte': self.min_count.data}

        if self.search_history.data:
            if self.search_history.data == 'True':
                match['usages'] = {'$gt': 0}
            else:
                match['usages'] = 0

        if match: pipeline.append({'$match': match})

        sort = {self.sort.data: [-1, 1][self.sort_order.data]}
        pipeline.append({'$sort': sort})

        return pipeline
