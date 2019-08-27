from typing import Dict

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, SelectField, IntegerField
from wtforms import validators

from swisstext.frontend.utils.search_form import SearchForm


class DeleteUrlForm(FlaskForm):
    delete = SubmitField('Remove sentences & blacklist URL')


class AddUrlForm(FlaskForm):
    url = StringField('URL', validators=[validators.DataRequired(), validators.URL()])
    add1 = SubmitField('Add URL')
    add2 = SubmitField('I am sure, add it.')


class SearchUrlsForm(SearchForm):
    search = StringField(
        render_kw=dict(placeholder='url part'),
        validators=[validators.Length(min=2), validators.Optional()]
    )
    min_count = IntegerField(
        'Min sentences',
        validators=[validators.Optional()],
        default=0
    )
    crawl_history = SelectField(
        'Crawls',
        choices=[('', 'any'), ('False', 'Never crawled'), ('True', 'Crawled at least once')],
        validators=[validators.Optional()]
    )

    sort = SelectField(
        'Order by',
        choices=[('url', 'A-Z'), ('delta_date', 'Last crawl date'), ('count', 'Sentences count')],
        default='delta_date'
    )
    sort_order = BooleanField('Ascending', default=False)

    def get_mongo_params(self, **kwargs) -> Dict:
        query_params = dict(**kwargs)

        if self.search.data:
            query_params['id__icontains'] = self.search.data.strip()

        if self.min_count.data and self.min_count.data > 0:
            query_params['count__gte'] = self.min_count.data

        if self.crawl_history.data:
            query_params['crawl_history__0__exists'] = self.crawl_history.data == 'True'

        return query_params


class DeleteUrlsForm(FlaskForm):
    i_understand = BooleanField('I know what I am doing')

    go = SubmitField('Delete')

    def validate(self):
        return self.go.data and self.i_understand.data

