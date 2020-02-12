from typing import Dict

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, SelectField, IntegerField
from wtforms import validators

from swisstext.frontend.utils.search_form import SearchForm


class SearchTextsForm(SearchForm):
    search = StringField(
        render_kw=dict(placeholder='text'),
        validators=[validators.Length(min=2), validators.Optional()]
    )
    url_count = IntegerField(
        'Min url count',
        validators=[validators.Optional()],
        default=0
    )
    sort = SelectField(
        'Order by',
        choices=[('date_added', 'Date added')],
        default='delta_date'
    )
    sort_order = BooleanField('Ascending', default=False)

    def get_mongo_params(self, **kwargs) -> Dict:
        query_params = dict(**kwargs)

        if self.search.data:
            query_params['text__icontains'] = self.search.data.strip()

        if self.url_count.data and self.url_count.data > 0:
            query_params[f'urls__{self.url_count.data}__exists'] = True

        return query_params


class DeleteUrlsForm(FlaskForm):
    i_understand = BooleanField('I know what I am doing')

    go = SubmitField('Delete')

    def validate(self):
        return self.go.data and self.i_understand.data

