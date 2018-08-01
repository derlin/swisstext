from flask import request, jsonify, render_template


def missing_param(message: str): return error(400, 'MissingParameterError', message)


def bad_param(message: str): return error(400, 'BadParameterError', message)


def unknown_server_error(message: str): return error(500, 'UnknownError', message)


def no_result_error(message: str): return error(500, 'NoResultError', message)


def error(status_code: int, cause: str, message: str):
    if request.content_type != 'application/json':
        if status_code == 404:
            return render_template('404.html'), 404
        else:
            return render_template('error.html', status_code=status_code, cause=cause, message=message)
    else:
        return jsonify({
            'status': status_code,
            'url': request.url,
            'cause': cause,
            'message': message,
        }), status_code


def message(message: str):
    return jsonify({'message': message}), 200
