class APIResponse:
    def __init__(self, data: object, status_code: int = 200):
        self.data = data
        self.status_code = status_code

    def to_dict(self):
        return {"status_code": self.status_code, "data": self.data}

    @classmethod
    def empty(cls):
        return cls("OK", 200)

    @classmethod
    def not_found(cls):
        return cls("Não encontrado", 404)

    @classmethod
    def wrap_error(cls, error: BaseException, status_code: int = 400):
        return cls(str(error), status_code)
