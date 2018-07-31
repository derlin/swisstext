from flask import Blueprint, redirect, url_for
from flask import request
from flask_login import login_required, current_user
from markupsafe import Markup

from swisstext.frontend.persistence.models import MongoSentence
from swisstext.frontend.utils.flash import flash_success, flash_info, flash_form_errors, flash_warning
from swisstext.frontend.utils.utils import templated
from .forms import KeywordsForm, OneForm, base_mongo_params

blueprint_labelling = Blueprint('labelling', __name__, template_folder='templates')


@blueprint_labelling.route('/bulk', methods=['GET', 'POST'])
@login_required
@templated('labelling/search.html')
def add_labels():
    sentences = []
    has_results = False

    if request.method == 'POST':
        form = KeywordsForm()

        if not form.validate():
            return dict(form=form)

        if form.save.data:
            saved_count = 0
            for k, v in request.form.items():
                if k.startswith('sentence-'):
                    MongoSentence.add_label(k[9:], uuid=current_user.id, label=v)
                    saved_count += 1
            flash_success("Labelled %d sentences." % saved_count)
            # don't use redirect_as_get since we have "hidden" sentence ids in the form...
            return form.redirect_after_save()
        else:
            return form.redirect_as_get()

    else:
        form = KeywordsForm.from_get()
        if not form.is_blank() and form.validate():
            extra_query = dict(text__icontains=form.search.data) if form.search.data else dict()
            sentences = MongoSentence.objects(
                deleted__exists=False,
                validated_by__exists=True,
                dialect__labels__user__ne=current_user.id,
                **extra_query) \
                .limit(form.per_page.data)

            has_results = True

        return dict(form=form, sentences=sentences, has_results=has_results)


# -----------------------------


@blueprint_labelling.route('', methods=['GET', 'POST'])
@login_required
@templated('labelling/one.html')
def add_labels_radio():
    form = OneForm()

    if request.method == 'POST':
        s = MongoSentence.objects.with_id(form.sentence_id.data)
        msg = "Sentence <a class='alert-link' href='%s'><code>%s</code></a>" % (
            url_for('sentences.details', sid=s.id), s.id)
        if s and form.validate():
            if form.delete_sentence.data:
                MongoSentence.mark_deleted(s, current_user.id)
                flash_warning(Markup(msg + " deleted."))
            elif form.dialect.data.startswith('?'):
                s.update(add_to_set__dialect__skipped_by=current_user.id)
                flash_info(Markup(msg + " skipped."))
            else:
                MongoSentence.add_label(s, label=form.dialect.data, uuid=current_user.id)
                flash_success(Markup(msg + " labelled."))
        else:
            flash_form_errors(form)

        return redirect(url_for(request.endpoint))

    else:
        sentence = MongoSentence.objects(**base_mongo_params()) \
            .fields(id=1, url=1, text=1) \
            .first()

        if sentence:
            form.sentence_id.data = sentence.id
            return dict(form=form, sentence=sentence)
        else:
            flash_warning('No more validated sentences to label. Please, help us by doing some validation :) ')
            return redirect(url_for('validation.validate'))
