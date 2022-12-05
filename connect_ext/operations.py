# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, CloudBlue
# All rights reserved.
#
import uuid
import random
from typing import Dict

from connect.client import AsyncConnectClient


async def _get_connection_id(
    client: AsyncConnectClient,
    hub_id: str,
    connection_type: str = 'production',
):
    if connection_type in ('development', 'preview'):
        return 'CT-0000-0000-0000'
    async for c in client.hubs[hub_id].connections.all():
        if c['type'] == connection_type:
            return c['id']


async def _get_request_body(
    product_id: str,
    connection_id: str,
    request_status: str = None,
    market_place_id: str = None,
    item: Dict = None,
    tiers: Dict = None,
):
    assert_uuid = str(uuid.uuid4())
    body = {
        "type": 'purchase',
        "asset": {
            "product": {
                "id": product_id,
            },
            "connection": {
                "id": connection_id,
            },
            "external_uid": assert_uuid,
            "external_id": assert_uuid,
        },
        "marketplace": {
            "id": market_place_id,
        },
    }
    if request_status:
        body['status'] = request_status
    if item:
        body['asset']['items'] = [item]
    if tiers:
        body['asset']['tiers'] = tiers
    return body


async def _get_tiers(client: AsyncConnectClient, account_id: str):
    f = f'eq(hub.id,null())&ne(parent.id,null())&owner.id={account_id}'
    tier = await client('tier').accounts.filter(f).order_by('name').first()
    tiers = {'customer': {'id': tier['id']}}
    if 'parent' in tier:
        tiers['tier1'] = {'id': tier['parent']['id']}
    return tiers


async def create_draft_request(
    client: AsyncConnectClient,
    connection_type: str,
    account_id: str,
    product_id: str,
    hub_id: str,
):
    f = f'owner.id={account_id}'
    marketplaces = ','.join([x['id'] async for x in client.marketplaces.filter(f)])
    f = f'in(contract.marketplace.id,({marketplaces}))&product.id={product_id}'
    market_place_id = (
        await client.listings.filter(f).all().first()
    )['contract']['marketplace']['id']

    tiers = await _get_tiers(client, account_id)

    item = await client.products[product_id].items.all().first()
    item['quantity'] = random.randint(60, 3000)

    connection_id = await _get_connection_id(client, hub_id, connection_type)

    body = await _get_request_body(
        product_id=product_id,
        request_status='draft',
        market_place_id=market_place_id,
        connection_id=connection_id,
        item=item,
        tiers=tiers,
    )
    response = await client.requests.create(payload=body)
    return response


async def change_draft_to_pending(client: AsyncConnectClient, request_id: str):
    response = await client.requests[request_id]('purchase').post()
    return response


async def create_change_request(
    client: AsyncConnectClient,
    product_id: str,
    request_id: str,
    asset_id: str,
):
    item = await client.products[product_id].items.all().first()
    item['quantity'] = random.randint(60, 3000)
    body = {
        'id': request_id,
        'type': 'change',
        'asset': {
            'id': asset_id,
            'items': [item],
        },
    }
    response = await client.requests.create(payload=body)
    return response


async def get_request_by_id(client: AsyncConnectClient, request_id: str):
    return await client.requests[request_id].get()


async def validate_request(client: AsyncConnectClient, request: Dict):
    response = await client.requests[request['id']]('validate').post(payload=request)
    return response


async def update_request(client: AsyncConnectClient, request_id: str, body: Dict):
    return await client.requests[request_id].update(payload=body)


async def create_request(client: AsyncConnectClient, request_type: str, asset_id: str):
    body = {
        'type': request_type,
        'asset': {'id': asset_id},
    }
    return await client.requests.create(payload=body)
