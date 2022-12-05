# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, Cloudblue connect
# All rights reserved.
#
import pytest

from connect_ext.events import HubTestingEventsApplication


@pytest.mark.asyncio
async def test_handle_asset_purchase_request_processing(
    async_connect_client,
    logger,
    mocker,
):
    request = {'id': 'PR-123', 'asset': {'id': 'AS-123'}}
    ext = HubTestingEventsApplication(async_connect_client, logger, {})
    ext.db = mocker.AsyncMock()
    ext.db.get_test_id_from_object_id = mocker.AsyncMock(return_value=1)
    result = await ext.handle_asset_purchase_request_processing(request)
    assert result.status == 'success'
    ext.db.get_test_id_from_object_id.assert_awaited()
    ext.db.check_step.assert_awaited_with(1, 'purchase', 'PR-123')


@pytest.mark.asyncio
async def test_handle_asset_adjustment_request_processing(
    async_connect_client,
    logger,
    mocker,
):
    request = {'id': 'PR-123', 'asset': {'id': 'AS-123', 'product': {'id': 'PRD-123'}}}
    ext = HubTestingEventsApplication(async_connect_client, logger, {})
    ext.db = mocker.AsyncMock()
    ext.db.get_test_id_from_object_id = mocker.AsyncMock(return_value=1)
    change_request = {'id': 'PR-123-002'}
    mocked_create_change_request = mocker.AsyncMock(return_value=change_request)
    mocker.patch('connect_ext.events.create_change_request', mocked_create_change_request)
    result = await ext.handle_asset_adjustment_request_processing(request)
    assert result.status == 'success'
    ext.db.update_step_object_id.assert_awaited_with(1, 'adjustment', request['id'])
    ext.db.check_step.assert_awaited_with(1, 'adjustment', request['id'])
    mocked_create_change_request.assert_awaited_with(
        client=ext.client,
        product_id='PRD-123',
        request_id=request['id'],
        asset_id='AS-123',
    )
    ext.db.add_new_step.assert_awaited_with('AS-123', 'change', change_request['id'])


@pytest.mark.asyncio
async def test_handle_asset_change_request_processing(
    async_connect_client,
    logger,
    mocker,
):
    request = {'id': 'PR-123', 'asset': {'id': 'AS-123'}}
    ext = HubTestingEventsApplication(async_connect_client, logger, {})
    ext.db = mocker.AsyncMock()
    ext.db.get_test_id_from_object_id = mocker.AsyncMock(return_value=1)
    change_request = {'id': 'PR-123-002'}
    mocked_create_request = mocker.AsyncMock(return_value=change_request)
    mocker.patch('connect_ext.events.create_request', mocked_create_request)
    result = await ext.handle_asset_change_request_processing(request)
    assert result.status == 'success'
    ext.db.check_step.assert_awaited_with(1, 'change', request['id'])
    mocked_create_request.assert_awaited_with(
        client=ext.client,
        request_type='suspend',
        asset_id='AS-123',
    )
    ext.db.add_new_step.assert_awaited_with('AS-123', 'suspend', change_request['id'])


@pytest.mark.asyncio
async def test_handle_asset_suspend_request_processing(
    async_connect_client,
    logger,
    mocker,
):
    request = {'id': 'PR-123', 'asset': {'id': 'AS-123'}}
    ext = HubTestingEventsApplication(async_connect_client, logger, {})
    ext.db = mocker.AsyncMock()
    ext.db.get_test_id_from_object_id = mocker.AsyncMock(return_value=1)
    change_request = {'id': 'PR-123-002'}
    mocked_create_request = mocker.AsyncMock(return_value=change_request)
    mocker.patch('connect_ext.events.create_request', mocked_create_request)
    result = await ext.handle_asset_suspend_request_processing(request)
    assert result.status == 'success'
    ext.db.check_step.assert_awaited_with(1, 'suspend', request['id'])
    mocked_create_request.assert_awaited_with(
        client=ext.client,
        request_type='resume',
        asset_id='AS-123',
    )
    ext.db.add_new_step.assert_awaited_with('AS-123', 'resume', change_request['id'])


@pytest.mark.asyncio
async def test_handle_asset_resume_request_processing(
    async_connect_client,
    logger,
    mocker,
):
    request = {'id': 'PR-123', 'asset': {'id': 'AS-123'}}
    ext = HubTestingEventsApplication(async_connect_client, logger, {})
    ext.db = mocker.AsyncMock()
    ext.db.get_test_id_from_object_id = mocker.AsyncMock(return_value=1)
    change_request = {'id': 'PR-123-002'}
    mocked_create_request = mocker.AsyncMock(return_value=change_request)
    mocker.patch('connect_ext.events.create_request', mocked_create_request)
    result = await ext.handle_asset_resume_request_processing(request)
    assert result.status == 'success'
    ext.db.check_step.assert_awaited_with(1, 'resume', request['id'])
    mocked_create_request.assert_awaited_with(
        client=ext.client,
        request_type='cancel',
        asset_id='AS-123',
    )
    ext.db.add_new_step.assert_awaited_with('AS-123', 'cancel', change_request['id'])


@pytest.mark.asyncio
async def test_handle_asset_cancel_request_processing_success(
    async_connect_client,
    logger,
    mocker,
):
    request = {'id': 'PR-123', 'asset': {'id': 'AS-123'}}
    ext = HubTestingEventsApplication(async_connect_client, logger, {})
    ext.db = mocker.AsyncMock()
    ext.db.get_test_id_from_object_id = mocker.AsyncMock(return_value=1)
    ext.db.get_steps_to_check = mocker.AsyncMock(return_value=[])
    ext.db.get_step_count = mocker.AsyncMock(return_value=6)
    result = await ext.handle_asset_cancel_request_processing(request)

    assert result.status == 'success'
    ext.db.check_step.assert_awaited_with(1, 'cancel', request['id'])
    ext.db.get_steps_to_check.assert_awaited_with(test_id=1)
    ext.db.get_step_count.assert_awaited_with(test_id=1)
    ext.db.set_test_result.assert_awaited_with(1, 'success')
