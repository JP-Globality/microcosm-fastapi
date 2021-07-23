from fastapi import HTTPException
from fastapi.responses import JSONResponse
from typing import Any
import functools

import functools
from fastapi import Request
from makefun import wraps

import traceback
from microcosm_fastapi.signature import extract_request_from_args, extract_request_from_kwargs, maybe_modify_signature
from microcosm_fastapi.utils import bind_to_request_state


DEFAULT_SERVER_STATUS_CODE = 500


class ErrorAdapter:
    def __init__(self, error: Any):
        self.error = error

    def __call__(self):
        """
        Converts a microcosm error into a http exception

        """
        return HTTPException(DEFAULT_SERVER_STATUS_CODE)


async def process_func(func, request, *args, **kwargs):
    bind_to_request_state(request, error=None, traceback=None)
    try:
        return await func(*args, **kwargs)
    except Exception as error:
        bind_to_request_state(request, error=error, traceback=traceback.format_exc(limit=10))
        adapter = ErrorAdapter(error)
        raise adapter()


def configure_error_adapter(graph):
    def error_adapter(func):
        new_sig, already_contains_request_arg = maybe_modify_signature(func)

        if already_contains_request_arg:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                new_args, request = extract_request_from_args(args)

                if request is None:
                    new_kwargs, request = extract_request_from_kwargs(**kwargs)

                return await process_func(func, request, new_args, new_kwargs)

        else:
            @wraps(func, new_sig=new_sig)
            async def wrapper(*args, **kwargs):
                new_args, request = extract_request_from_args(args, remove_from_args=True)

                if request is None:
                    new_kwargs, request = extract_request_from_kwargs(**kwargs, remove_from_kwargs=True)

                return await process_func(func, request, new_args, new_kwargs)

        return wrapper
    return error_adapter