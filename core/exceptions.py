class AppError(Exception):
    status_code = 400

    def __init__(self, detail):
        super().__init__(detail)
        self.detail = detail


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class ForbiddenError(AppError):
    status_code = 403


class InvalidDataError(AppError):
    status_code = 422