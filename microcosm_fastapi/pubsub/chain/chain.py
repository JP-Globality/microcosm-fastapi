from inspect import iscoroutinefunction
import sys
from microcosm_pubsub.chain.chain import Chain

from microcosm_fastapi.pubsub.chain.context_decorators import (
    get_from_context_async,
    save_to_context_async,
    save_to_context_by_func_name_async,
    temporarily_replace_context_keys_async,
)


class ChainAsync(Chain):
    """
    Chain handler that works with both non-async and async methods
    that are chained together.

    The __call__ contract is therefore an async coroutine but blocking/async performance
    will mirror the underlying called functions.

    """
    @property
    def context_decorators(self):
        """
        Decorators to apply to the chain links. Rely on decorators that also have optional
        async support depending on the function signature.
        """
        return [
            # Order matter - get_from_context should be first
            get_from_context_async,
            temporarily_replace_context_keys_async,
            save_to_context_async,
            save_to_context_by_func_name_async,
        ]

    async def __call__(self, context=None, **kwargs):
        """
        Resolve the chain and return the last chain function result
        :param context: use existing context instead of creating a new one
        :param **kwargs: initialize the context with some values
        """
        context = context or self.new_context_type()
        context.update(kwargs)

        res = None

        for link in self.links:
            func = self.apply_decorators(context, link)

            if iscoroutinefunction(func):
                res = await func()
            elif hasattr(link, '__call__') and hasattr(func, 'async_call') and func.async_call:
                # we check link.__call__ as the self.apply_decorators changes
                # the ability to check the func method call, resulting in iscoroutinefunction(func)
                # being False when we actually have a coroutinefuncion

                # TODO - workout why we end up with a list -> e.g [<coroutine object ExtractSuggestionGoalDescriptors.__call__ at 0x10fa248c0>]
                # and hence we have to do this hacky stuff
                res1 = func()
                res2 = res1[0]
                res = await res2
            else:
                res = func()

        return res

    def from_coroutine():
        return sys._getframe(2).f_code.co_flags & 0x380
