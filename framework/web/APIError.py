class APIError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        return {"message": self.message, "status_code": self.status_code}
