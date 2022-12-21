# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, CloudBlue
# All rights reserved.
#
import pytest

from connect_ext.operations import (
    change_draft_to_pending,
    create_change_request,
    create_draft_request,
    create_request,
    get_request_by_id,
    update_request,
    validate_request,
)


@pytest.mark.asyncio
async def test_create_draft_request(
    async_client_mocker_factory,
    async_connect_client,
):
    account_id = 'VA-123-123'
    product_id = 'PRD-123'
    hub_id = 'HUB-123'
    client = async_client_mocker_factory()
    client.marketplaces.filter(f'owner.id={account_id}').mock(
        return_value=[{'id': 'MK-123'}],
    )
    f = f'in(contract.marketplace.id,(MK-123))&product.id={product_id}'
    client.listings.filter(f).all().first().mock(
        return_value=[
            {
                'contract': {
                    'marketplace': {
                        'id': 'MK-123',
                    },
                },
            },
        ],
    )
    f = f'eq(hub.id,null())&ne(parent.id,null())&owner.id={account_id}'
    client('tier').accounts.filter(f).order_by('name').first().mock(
        return_value=[{
            'id': 'TA-123',
            'parent': {
                'id': 'TA-223',
            },
        }],
    )
    client.products[product_id].items.all().first().mock(
        return_value=[{
            'id': 'IT-123',
            'quantity': 22,
        }],
    )
    client.hubs[hub_id].connections.all().mock(
        return_value=[
            {
                'type': 'production',
                'id': 'CT-123-123',
            },
        ],
    )

    expected = {'id': 'PR-123', 'type': 'purchase'}
    client.requests.create(return_value=expected)
    response = await create_draft_request(
        async_connect_client,
        'production',
        account_id,
        product_id,
        hub_id,
    )
    assert response == expected


@pytest.mark.asyncio
async def test_change_draft_to_pending(
    async_client_mocker_factory,
    async_connect_client,
):
    request_id = 'PR-123'
    client = async_client_mocker_factory()
    expected = {'id': 'PR-123', 'type': 'purchase', 'status': 'draft'}
    client.requests[request_id]('purchase').post(return_value=expected)
    response = await change_draft_to_pending(
        async_connect_client,
        request_id,
    )
    assert response == expected


@pytest.mark.asyncio
async def test_create_change_request(
    async_client_mocker_factory,
    async_connect_client,
):
    product_id = 'PRD-123'
    request_id = 'PR-123'
    asset_id = 'AS-123'
    client = async_client_mocker_factory()
    client.products[product_id].items.all().first().mock(
        return_value=[{'id': 'IT-123', 'quantity': 33}],
    )
    expected = {'id': 'PR-123', 'type': 'change', 'status': 'draft'}
    client.requests.create(return_value=expected)
    response = await create_change_request(
        async_connect_client,
        product_id,
        request_id,
        asset_id,
    )
    assert response == expected


@pytest.mark.asyncio
async def test_get_request_by_id(
    async_client_mocker_factory,
    async_connect_client,
):
    request_id = 'PR-123'
    client = async_client_mocker_factory()
    expected = {'id': 'PR-123', 'type': 'change', 'status': 'pending'}
    client.requests[request_id].get(return_value=expected)
    response = await get_request_by_id(
        async_connect_client,
        request_id,
    )
    assert response == expected


@pytest.mark.asyncio
async def test_validate_request(
    async_client_mocker_factory,
    async_connect_client,
):
    request_id = 'PR-123'
    client = async_client_mocker_factory()
    request = {'id': request_id, 'type': 'purchase', 'status': 'draft'}
    client.requests[request_id]('validate').post(return_value=request, match_body=request)
    response = await validate_request(
        async_connect_client,
        request,
    )
    assert response == request


@pytest.mark.asyncio
async def test_update_request(
    async_client_mocker_factory,
    async_connect_client,
):
    request_id = 'PR-123'
    client = async_client_mocker_factory()
    body = {'id': 'PR-123', 'type': 'change', 'status': 'pending'}
    client.requests[request_id].update(return_value=body, match_body=body)
    response = await update_request(
        async_connect_client,
        request_id,
        body,
    )
    assert response == body


@pytest.mark.asyncio
async def test_create_request(
    async_client_mocker_factory,
    async_connect_client,
):
    request_type = 'adjustment'
    asset_id = 'AS-123'
    client = async_client_mocker_factory()
    body = {
        'type': request_type,
        'asset': {'id': asset_id},
    }
    client.requests.create(return_value={}, match_body=body)
    response = await create_request(
        async_connect_client,
        request_type,
        asset_id,
    )
    assert response == {}
