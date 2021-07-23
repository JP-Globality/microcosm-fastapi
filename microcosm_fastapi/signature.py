"""
Functions to do with modifying/updating function signatures

"""
import functools
from fastapi import Request
from makefun import wraps
from inspect import signature, Parameter
from copy import deepcopy, copy


def extract_request_from_args(args, remove_from_args: bool = False):
    """
    Extracts the request value from args and maybe removes it

    """
    request = None
    copied_args = [*args]
    for index, arg in enumerate(args):
        if isinstance(arg, Request):
            request = arg
            if remove_from_args:
                copied_args.pop(index)

    return copied_args, request


def extract_request_from_kwargs(remove_from_kwargs: bool = False, **kwargs):
    """
    Extracts the request value from kwargs and maybe removes it

    """
    # TODO - mutating kwargs so we no longer have kwargs inside other decorators
    new_kwargs = copy(kwargs)
    request = None
    for key, value in new_kwargs.items():
        if key == 'request' and isinstance(value, Request):
            request = new_kwargs['request']

    if remove_from_kwargs and request is not None:
        del new_kwargs['request']

    return new_kwargs, request


def maybe_modify_signature(func):
    """
    Maybe modifies signature of function to include the request:Request argument
    """
    old_signature = signature(func)

    new_signature = deepcopy(old_signature)
    params = list(new_signature.parameters.values())
    has_request_param = False
    for param in params:
        if param.name == 'request':
            has_request_param = True

    if not has_request_param:
        params.append(Parameter('request', kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=Request))
        return new_signature.replace(parameters=params), has_request_param

    return new_signature, has_request_param