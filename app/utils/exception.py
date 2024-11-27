
class MessageException(Exception):
    def __init__(self, 
                 message="An error occurred", 
                 status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __str__(self):
        return self.message
