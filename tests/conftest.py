# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, Cloudblue connect
# All rights reserved.
#
import os

import pytest
from connect.client import AsyncConnectClient, ConnectClient

from connect_ext.db import DB


@pytest.fixture
def connect_client():
    return ConnectClient(
        'ApiKey fake_api_key',
        endpoint='https://example.org/public/v1',
    )


@pytest.fixture
def async_connect_client():
    return AsyncConnectClient(
        'ApiKey fake_api_key',
        endpoint='https://example.org/public/v1',
    )


@pytest.fixture
def logger(mocker):
    return mocker.MagicMock()


@pytest.fixture(autouse=True)
def db(mocker):
    yield mocker.patch('connect_ext.db.db', DB(':memory:'))


@pytest.fixture(autouse=True)
def patch_api_key(mocker):
    mocker.patch.dict(os.environ, {'API_KEY': 'ApiKey API_KEY'})
    yield
