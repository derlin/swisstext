from flask import Blueprint, redirect, url_for, render_template
from flask import request
from flask_login import login_required, current_user
from markupsafe import Markup

from swisstext.frontend.persistence.models import MongoSentence, MongoURL
from swisstext.frontend.utils.flash import *
from swisstext.frontend.utils.utils import templated
from .forms import KeywordsForm, OneForm, FromUrlPostForm, base_mongo_params

blueprint_labelling = Blueprint('labelling', __name__, template_folder='templates')


@blueprint_labelling.route('/from_url', methods=['GET', 'POST'])
@login_required
@templated('labelling/from_url.html')
def label_from_url():
    param_uid = request.args.get('uid', '')
    param_sid = request.args.get('sid', '')

    if not param_uid:
        # no url specified: redirect to single labelling view
        flash_error('No url specified.')
        return redirect(url_for('.label_one', id=param_sid))

    form = FromUrlPostForm()
    if request.method == 'POST':  # we have a post: save the labels
        if not form.validate():
            flash_form_errors(form)
        elif form.save.data:
            saved_count = _label_all_from_form(request.form)
            flash_success("Labelled %d sentences." % saved_count)
        # redirect as GET
        return redirect(url_for(request.endpoint, dialect=form.dialect.data, uid=param_uid))
    else:  # this is a get: display the form to label all urls from the uid
        # first, get the URL object
        mu = MongoURL.get(id=param_uid)
        if mu is None:
            # non-existant URL: redirect to single labelling view
            flash_warning(Markup(f'The URL <code>{param_uid}</code> does not exist.'))
            return redirect(url_for('.label_one'))
        # Now, get the sentences from the url, ordered by date_added
        sentences = MongoSentence.objects(**base_mongo_params(), url=mu.url) \
            .order_by('date_added') \
            .paginate(page=1, per_page=50)
        if sentences.total == 0:
            # no sentences, redirect to single labelling view
            flash_warning(Markup(f'No sentence left to label for URL  <code>{param_uid}</code>.<br>'
                                 '<small>Either they are not validated or you already labelled them</small>.'))
            return redirect(url_for('.label_one'))
        # set default dialect and return
        form.dialect.data = request.args.get('dialect', '')
        return dict(form=form, param_sid=param_sid, url=mu.url, sentences=sentences)


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
            saved_count = _label_all_from_form(request.form)
            flash_success("Labelled %d sentences." % saved_count)
            # don't use redirect_as_get since we have "hidden" sentence ids in the form...
            return form.redirect_after_save()
        else:
            return form.redirect_as_get()

    else:
        form = KeywordsForm.from_get()
        if not form.is_blank() and form.validate():
            sentences = MongoSentence.objects(**form.get_mongo_params()) \
                .order_by('url', 'date_added') \
                .limit(form.per_page.data)
            has_results = True

        return dict(form=form, sentences=sentences, has_results=has_results)


# -----------------------------


@blueprint_labelling.route('', methods=['GET', 'POST'])
@login_required
@templated('labelling/one.html')
def label_one():
    form = OneForm()

    if request.method == 'POST': # try saving the dialect
        s = MongoSentence.objects.with_id(form.sentence_id.data)
        msg = "Sentence <a class='alert-link' href='%s'><code>%s</code></a>" % (
            url_for('sentences.details', sid=s.id), s.id)
        if s and form.validate():
            if form.delete_sentence.data:
                # mark the sentence as deleted.
                MongoSentence.mark_deleted(s, current_user.id)
                flash_warning(Markup(msg + " deleted."))
            else:
                if form.dialect.data.startswith('?'):
                    # mark the sentence as swipped by this user
                    s.dialect.skip(uuid=current_user.id)
                    flash_info(Markup(msg + " skipped."))
                else:
                    # add the label tag
                    s.dialect.add_label(uuid=current_user.id, label=form.dialect.data)
                    flash_success(Markup(msg + " labelled <i>%s</i>." % form.dialect.data))
        else:
            flash_form_errors(form)

        return redirect(url_for(request.endpoint))

    else: # we have a get
        id = request.args.get('id', None)
        current_label = None # current label previously assigned by this user (None = not labelled yet)
        if id: # a specific sentence is requested
            # we got a specific sentence from the request parameters
            sentence = MongoSentence.objects(id=id).get_or_404()
            if len(sentence.validated_by) == 0:
                # the sentence is not validated, do it fist
                flash_warning("The sentence should be validated first.")
                return redirect(url_for('sentences.details', sid=sentence.id))
            else:
                # the sentence is validated, check if this user already did something (skipped or labelled it)
                if sentence.dialect:
                    if sentence.dialect.skipped_by and current_user.id in sentence.dialect.skipped_by:
                        current_label = '?'
                    elif sentence.dialect.labels:
                        for d in sentence.dialect.labels:
                            if d.user == current_user.id:
                                current_label = d.label
        else:
            # no specific sentence, just pick one validated sentence at random
            sentence = MongoSentence.objects(**base_mongo_params()) \
                .fields(id=1, url=1, text=1) \
                .order_by('url', 'date_added') \
                .first()

            if not sentence:
                flash_warning('No more validated sentences to label. Please, help us by doing some validation :) ')
                return redirect(url_for('validation.validate'))

        # TODO here, we count only validated sentences not labelled by the user... Is it ok ?
        sentences_count = MongoSentence.objects(url=sentence.url, **base_mongo_params()).count()

        form.sentence_id.data = sentence.id
        form.current_label.data = current_label

        return dict(form=form, sentence=sentence, sentences_count=sentences_count)


def _label_all_from_form(form):
    saved_count = 0
    for k, v in form.items():
        # labelled sentences have key = sentence-<sid> and value = <label_name>
        if k.startswith('sentence-'):
            s = MongoSentence.objects.with_id(k[9:]) # 9 = len('sentence-')
            if v.startswith('?'): # this is the value for the "No Idea" option
                s.dialect.skip(uuid=current_user.id)
            else:
                s.dialect.add_label(uuid=current_user.id, label=v)
            saved_count += 1
    return saved_count
