"""
Audit log support for FastAPI routes.

"""
import functools
from fastapi import Request
from makefun import wraps
from inspect import signature, Parameter
from copy import deepcopy, copy


def maybe_modify_signature(sig):
    """
    Maybe modifies signature of function to include the request:Request argument
    """
    new_sig = deepcopy(sig)
    params = list(new_sig.parameters.values())
    has_request_param = False
    for param in params:
        if param.name == 'request':
            has_request_param = True

    if not has_request_param:
        params.append(Parameter('request', kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=Request))
        return new_sig.replace(parameters=params), has_request_param

    return new_sig, has_request_param


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
        sig = signature(func)
        new_sig, already_contains_request_arg = maybe_modify_signature(sig)

        if already_contains_request_arg:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # We need to leave the request argument inside args/kwargs
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg

                if request is None:
                    for key, value in kwargs.items():
                        if key == 'request' and isinstance(value, Request):
                            request = kwargs['request']

                # Bind operation name and func name to request state
                request.state.func_name = func.__name__
                request.state.operation_name = operation_name
                return await func(*args, **kwargs)

        else:
            @wraps(func, new_sig=new_sig)
            async def wrapper(*args, **kwargs):
                # We need to remove the request argument from args/kwargs
                request = None
                new_args = []
                for arg in args:
                    if not isinstance(arg, Request):
                        new_args.append(arg)
                    else:
                        request = arg

                new_kwargs = copy(kwargs)
                if request is None:
                    for key, value in new_kwargs.items():
                        if key == 'request' and isinstance(value, Request):
                            request = kwargs['request']
                            del kwargs['request']

                # Bind operation name and func name to request state
                request.state.func_name = func.__name__
                request.state.operation_name = operation_name
                return await func(*args, **kwargs)

        return wrapper
    return request_state_binder
