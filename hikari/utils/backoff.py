#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import functools
import logging
import random

from typing import Callable, Collection, Optional, Type

import async_timeout

_LOGGER = logging.getLogger(__name__)


class RetryExpiredError(RuntimeError):
    """
    Raised if max retries or timeout was hit.

    Args:
        message: the message to show.
    """
    __slots__ = ()

    def __init__(self, message: str) -> None:
        super().__init__(message)


def retry(*,
          backoff_base: float = 2,
          transform: Callable[[float, int], float] = lambda base, increment: base ** increment,
          jitter: Callable[[float], float] = lambda backoff: ((random.random() * 2) - 1) * 0.1 * backoff,
          max_retries: Optional[int] = float('inf'),
          timeout: Optional[float] = float('inf'),
          retry_on: Collection[Type[Exception]] = (Exception,),
          fatal_on: Collection[Type[Exception]] = (asyncio.CancelledError,)):
    r"""
    Decorates a coroutine function or regular function and produces a coroutine function decorator of that function.

    Perform some form of back-off every time certain exceptions are raised. By default this uses exponential back-off
    with a base of 2 and 10% jitter, and will continue to back-off increasingly forever.

    >>> @retry(max_retries=5)
    ... async def send_request(url):
    ...     async with aiohttp.request('get', url) as resp:
    ...         resp.raise_for_status()
    ...         return await resp.json()

    The latter example would produce a coroutine function that takes a URL argument and attempts
    to hit the URL with at most 5 failures before giving up and propagating the exception.

    Args:
        backoff_base:
            The backoff base time period to apply to each time. This defaults to 2.
        transform:
            A function that takes the base and the number of previous retries and outputs a base backoff to sleep for.
            This defaults to exponential backoff, that is, :math`b^{i}` such that :math:`b` is the base, and :math:`i`
            is the increment.
        jitter:
            A function that takes the base backoff and returns the amount of jitter to apply to the backoff. This allows
            for random jitter to be applied. The default is to apply :math:`\pm 0.1b` jitter if unspecified.
            To use no jitter, provide :code:`lambda _: 0` as the argument.
        max_retries:
            The maximum number of retries to make after the first initial failure (inclusive) before failing completely.
            Defaults to infinity.
        timeout:
            The maximum backoff to wait for (exclusive) before failing completely. Defaults to infinity.
        retry_on:
            A collection of types deriving from `Exception`. If any of these are raised, and are not in the `fatal_on`
            collection (either directly or as a derived type from), then we are guaranteed to retry if the `max_retries`
            and `max_timeout` have not been reached. Defaults to just :class:`Exception`, thus matching any exception
            type derived from that, but ignoring low level exceptions such as assertion failures and keyboard
            interrupts.
        fatal_on:
            A collection of covariant exception types to always fail on, even if they are matched by `retry_on`. Like
            `retry_on`, this is used with covariant type matching. This is useful for edge cases you want to exit on
            even if base types are in the `retry_on` collection. Defaults to just :class:`asyncio.CancelledError`.

    Returns:
        The result provided by the decorated coroutine function.

    Raises:
        RetryExpiredError: if all retries failed.
        asyncio.TimeoutError: if the timeout was hit.
    """
    def decorator(coroutine_function):
        name = getattr(coroutine_function, '__name__', str(coroutine_function))
        coroutine_function = asyncio.coroutine(coroutine_function)

        @functools.wraps(coroutine_function)
        async def back_off_wrapper(*args, **kwargs):
            retry, ex = 0, None
            async with async_timeout.timeout(timeout):
                while retry <= max_retries:
                    try:
                        _LOGGER.debug("Calling %s (retry #%s)", name, retry)
                        return await coroutine_function(*args, **kwargs)
                    except fatal_on as ex:
                        raise ex
                    except retry_on as ex:
                        backoff = transform(backoff_base, retry)
                        backoff += jitter(backoff)

                        retry += 1

                        if _LOGGER.level <= logging.DEBUG:
                            _LOGGER.exception("Exception caught while processing %s: will backoff for %ss and retry...",
                                              name, backoff, exc_info=ex)

                        await asyncio.sleep(backoff)
                    except Exception as ex:
                        # Base case, same as fatal_on.
                        raise ex
            raise RetryExpiredError(f"Gave up after maximum {retry} retries") from ex
        return back_off_wrapper
    return decorator


def centisecond_transform(base, increment):
    """
    Centi-second-granularity transformation for exponential backoff.
    
    Considering a base of 2 centi-second (10ms), it will backoff for 1cs, 2cs, 4cs, 8cs, 16cs, 32cs, 64cs, ...   
    """
    base *= 100
    base **= increment
    base /= 100
    return base


def default_network_connectivity_backoff(**kwargs):
    """
    Applies the default backoff used internal network-connectivity-based tasks within this library.
    
    This will timeout after 10 seconds, or 10 retries, and will use a centi-second exponential backoff with default
    10% jitter and default exceptions.  
    
    Args:
        kwargs: any defaults to override. All arguments get passed to :func:`retry`.
        
    Returns:
         A decorator.
    """
    for k, v in dict(backoff_base=0.02, backoff_unit=0.01, max_retries=10, 
                     timeout=10, transform=centisecond_transform).items(): 
        kwargs.setdefault(k, v)
        
    return retry(**kwargs)
