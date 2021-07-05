"""
Helper functions for pubsub daemons

"""
from functools import partial, wraps
from asyncio import get_event_loop
from inspect import signature


def create_partial(fn, **kwargs):
    return partial(fn, **kwargs)


def create_as_async_normal_fn(sync_fn):
    # decorator to make sync function async
    async def async_run(*args, **kwargs):
        loop = get_event_loop()
        request_func = create_partial(sync_fn, *args, **kwargs)
        return await loop.run_in_executor(None, request_func)

    return async_run


# https://stackoverflow.com/questions/11954037/dynamically-define-functions-with-varying-signature
def create_as_async(sync_callable):
    # decorator to make sync function async
    arg_names = sync_callable.__call__.__code__.co_varnames
    # Removing self from args
    filtered_arg_names = [i for i in arg_names if "self" != i]

    kwargs = {}
    sig = signature(sync_callable)
    for key, value in sig.parameters.items():
        kwargs["key"] = value.default

    async def async_run():
        sig = signature(sync_callable)
        loop = get_event_loop()
        request_func = create_partial(sync_callable, **kwargs)
        return await loop.run_in_executor(None, request_func)

    fn = create_partial(async_run, **kwargs)
    return fn