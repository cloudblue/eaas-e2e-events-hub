# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, CloudBlue
# All rights reserved.
#
import functools
import inspect
from datetime import datetime
import pprint
import traceback

from fastapi.responses import JSONResponse
from fastapi import status
from connect.client import ClientError


def _send_notification(msg, kwargs):
    if 'logger' in kwargs:
        kwargs['logger'].info(msg)


def safe_client(
    response_func=lambda x: JSONResponse(content=x, status_code=status.HTTP_400_BAD_REQUEST),
):
    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except ClientError as error:
                    msg = (
                        f'{error}\n'
                        f'Exception occured at: {datetime.now()}\n '
                        f'{pprint.pformat(traceback.format_exc())}',
                    )
                    _send_notification(msg, kwargs)
                    if response_func:
                        return response_func(msg)
                    raise
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except ClientError as error:
                    msg = (
                        f'{error}\n'
                        f'Exception occured at: {datetime.now()}\n '
                        f'{pprint.pformat(traceback.format_exc())}',
                    )
                    _send_notification(msg, kwargs)
                    if response_func:
                        return response_func(msg)
                    raise
        return wrapper

    return decorator
