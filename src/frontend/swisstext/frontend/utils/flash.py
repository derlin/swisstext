from flask import flash


def flash_form_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u" %s - %s" % (
                getattr(form, field).label.text,
                error
            ), 'danger')


def flash_error(msg):
    flash(msg, 'danger')


def flash_success(msg):
    flash(msg, 'success')


def flash_warning(msg):
    flash(msg, 'warning')


def flash_info(msg):
    flash(msg, 'info')
