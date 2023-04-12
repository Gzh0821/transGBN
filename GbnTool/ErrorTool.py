class CRCError(ValueError):
    def __init__(self, message: str, *args):
        super().__init__(message, *args)
        self.message = message

    def __str__(self):
        return f"CRC Check Error: {self.message}"
