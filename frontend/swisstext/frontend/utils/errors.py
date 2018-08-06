class AppError(Exception):

    def __init__(self, cause="AppError", message="", status_code=500):
        Exception.__init__(self)
        self.cause = cause
        self.status_code = status_code
        self.message = message


class ValidationError(AppError):
    def __init__(self, message):
        AppError.__init__(self, status_code=400, message=message)
