from fastapi import HTTPException
from typing import Any
import functools


class ErrorAdapter:
    def __init__(self, error: Any):
        self.error = error

    def __call__(self):
        """
        Converts a microcosm error into a http exception

        """
        return HTTPException(status_code=self.error.status_code, detail=str(self.error))


def error_adapter(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            response = await func(*args, **kwargs)
        except Exception as error:
            adapter = ErrorAdapter(error)
            raise adapter()

        return response
    return wrapper
