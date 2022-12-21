# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, CloudBlue
# All rights reserved.
#
import pytest

from connect_ext.decorators import safe_client

from connect.client import ClientError


def test_sync_safe_client(mocker):
    mocked_function = mocker.MagicMock(return_value='hello')

    @safe_client(response_func=mocked_function)
    def func():
        raise ClientError()

    result = func()
    assert result == 'hello'
    assert mocked_function.called is True


@pytest.mark.asyncio
async def test_async_safe_client(mocker):
    mocked_function = mocker.MagicMock(return_value='hello')

    @safe_client(response_func=mocked_function)
    async def func():
        raise ClientError()

    result = await func()
    assert result == 'hello'
    assert mocked_function.called is True
