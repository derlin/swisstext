from typing import Dict

from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectMultipleField, widgets, validators, SelectField, \
    BooleanField, StringField

from persistence.models import Dialects
from utils.search_form import SearchForm


class DeleteSentenceForm(FlaskForm):
    comment = StringField('comment', render_kw=dict(placeholder="optional comment"))
    delete = SubmitField('Go ahead!')


class SentencesForm(SearchForm):
    search = StringField(
        'Search',
        validators=[validators.Optional(), validators.Length(min=2)]
    )
    validated_only = BooleanField('Validated sentences only', default=False)
    labelled_only = BooleanField('Labelled sentences only', default=False)

    dialects = SelectMultipleField(
        'Dialects',
        choices=list(Dialects.items()),
        default=[],  # Dialects.items.keys(),
        validators=[validators.Optional()],
        widget=widgets.ListWidget(prefix_label=False),
        option_widget=widgets.CheckboxInput()
    )

    sort = SelectField(
        'Order by',
        choices=[('text', 'A-Z'), ('crawl_proba', 'SG proba'), ('url', 'url'), ('date_added', 'Date added')],
        default='date_added'
    )
    sort_order = BooleanField('Ascending', default=False)

    def get_mongo_params(self, **kwargs) -> Dict:
        query_params = dict(**kwargs)

        if len(self.dialects.data):
            if len(self.dialects.data) < len(self.dialects.choices):
                query_params['dialect__label__in'] = self.dialects.data
            else:
                query_params['dialect__label__exists'] = True

        if self.search.data:
            query_params['text__icontains'] = self.search.data.strip()

        if self.validated_only.data:
            query_params['validated_by__0__exists'] = True
        if self.labelled_only.data:
            query_params['dialect__label__exists'] = True

        return query_params
