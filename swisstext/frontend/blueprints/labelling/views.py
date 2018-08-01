from flask import Blueprint, redirect, url_for, render_template
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
                    MongoSentence.objects.with_id(k[9:]) \
                        .dialect \
                        .add_label(uuid=current_user.id, label=v)
                    saved_count += 1
            flash_success("Labelled %d sentences." % saved_count)
            # don't use redirect_as_get since we have "hidden" sentence ids in the form...
            return form.redirect_after_save()
        else:
            return form.redirect_as_get()

    else:
        form = KeywordsForm.from_get()
        if not form.is_blank() and form.validate():
            sentences = MongoSentence.objects(**form.get_mongo_params()) \
                .limit(form.per_page.data)
            has_results = True

        return dict(form=form, sentences=sentences, has_results=has_results)


# -----------------------------


@blueprint_labelling.route('', methods=['GET', 'POST'])
@login_required
@templated('labelling/one.html')
def label_one():
    form = OneForm()

    if request.method == 'POST':
        s = MongoSentence.objects.with_id(form.sentence_id.data)
        msg = "Sentence <a class='alert-link' href='%s'><code>%s</code></a>" % (
            url_for('sentences.details', sid=s.id), s.id)
        if s and form.validate():
            if form.delete_sentence.data:
                MongoSentence.mark_deleted(s, current_user.id)
                flash_warning(Markup(msg + " deleted."))
            else:
                if form.dialect.data.startswith('?'):
                    s.dialect.skip(uuid=current_user.id)
                    flash_info(Markup(msg + " skipped."))
                else:
                    s.dialect.add_label(uuid=current_user.id, label=form.dialect.data)
                    flash_success(Markup(msg + " labelled <i>%s</i>." % form.dialect.data))
        else:
            flash_form_errors(form)

        return redirect(url_for(request.endpoint))

    else:
        id = request.args.get('id', None)
        current_label = None
        if id:
            # we got a specific sentence from the request parameters
            sentence = MongoSentence.objects.with_id(id)
            if not sentence:
                flash_warning("sentence with id '%s' does not exist." % id)
                return render_template('404.html')

            elif len(sentence.validated_by) == 0:
                flash_warning("The sentence should be validated first.")
                return redirect(url_for('sentences.details', sid=sentence.id))
            else:
                if sentence.dialect:
                    if sentence.dialect.skipped_by and current_user.id in sentence.dialect.skipped_by:
                        current_label = '?'
                    elif sentence.dialect.labels:
                        for d in sentence.dialect.labels:
                            if d.user == current_user.id:
                                current_label = d.label
        else:
            # just pick one validated sentence at random
            sentence = MongoSentence.objects(**base_mongo_params()) \
                .fields(id=1, url=1, text=1) \
                .first()
            if not sentence:
                flash_warning('No more validated sentences to label. Please, help us by doing some validation :) ')
                return redirect(url_for('validation.validate'))

        form.sentence_id.data = sentence.id
        form.current_label.data = current_label
        return dict(form=form, sentence=sentence)
