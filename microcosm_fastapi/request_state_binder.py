"""
Request binder for func and operation name

"""
import functools
from fastapi import Request
from makefun import wraps

from microcosm_fastapi.signature import extract_request_from_args, extract_request_from_kwargs, maybe_modify_signature
from microcosm_fastapi.utils import bind_to_request_state


async def process_func(func, request, operation_name, *args, **kwargs):
    bind_to_request_state(request, func_name=func.__name__, operation_name=operation_name)
    return await func(*args, **kwargs)


def configure_request_state_binder(graph):
    """
    Bind operation name and function name to request state

    A lot of this function does dynamic adding/removing of the request:Request parameter
    which Starlette provides. The reason for this is that we need the request object
    inside our audit function but sometimes the actual controller being wrapped doesn't
    require the request argument. The way that Starlette decides if it needs to give you the
    request argument is by looking at the function signature so the functionality below is all
    about injecting the request argument inside the signature and then removing it later on
    when the actual controller function is called hence the so called "magic".

    The benefit of using this function is that we don't have to specify request:Request as a
    function argument in every single controller which is what we'd have to do without this "magic".

    """
    def request_state_binder(func, operation_name):
        new_sig, already_contains_request_arg = maybe_modify_signature(func)

        if already_contains_request_arg:
            # If the func args/kwargs already contain request, then we leave it in
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                new_args, request = extract_request_from_args(args)

                if request is None:
                    new_kwargs, request = extract_request_from_kwargs(**kwargs)

                return await process_func(func, request, operation_name, new_args, new_kwargs)

        else:
            # If the func args/kwargs don't already contain request, then we remove it
            @wraps(func, new_sig=new_sig)
            async def wrapper(*args, **kwargs):
                new_args, request = extract_request_from_args(args, remove_from_args=True)

                if request is None:
                    new_kwargs, request = extract_request_from_kwargs(**kwargs, remove_from_kwargs=True)

                return await process_func(func, request, operation_name, new_args, new_kwargs)

        return wrapper
    return request_state_binder
