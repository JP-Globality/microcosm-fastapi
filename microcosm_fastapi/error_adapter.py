from fastapi import HTTPException
from fastapi.responses import JSONResponse
from typing import Any
import functools

DEFAULT_SERVER_STATUS_CODE = 500

class ErrorAdapter:
    def __init__(self, error: Any):
        self.error = error

    def __call__(self):
        """
        Converts a microcosm error into a http exception

        """
        status_code = None
        try:
            status_code = self.error.status_code
        except AttributeError:
            pass
        # return JSONResponse(status_code = self.error.status_code, content = {"error": str(self.error), "message": "Something critical happened"})
        return HTTPException(status_code=status_code or DEFAULT_SERVER_STATUS_CODE)

# Currently not in use but we want to move the stuff from request_state_binder into
# this function (just need to generalise the adding/removing/updating of the request:Request
# argument first...
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
