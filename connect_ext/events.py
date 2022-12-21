# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, CloudBlue
# All rights reserved.
#
from connect.eaas.core.decorators import (
    event,
)
from connect.eaas.core.extension import EventsApplicationBase
from connect.eaas.core.responses import (
    BackgroundResponse,
)

from connect_ext.decorators import safe_client
from connect_ext.db import get_db
from connect_ext.operations import (
    create_change_request,
    create_request,
)
from connect_ext.models import ResultType


class HubTestingEventsApplication(EventsApplicationBase):

    def __init__(self, client, logger, config):
        super().__init__(client, logger, config)
        self.db = get_db()
        self.db.logger = logger

    @event(
        'asset_purchase_request_processing',
        statuses=[
            'approved',
        ],
    )
    @safe_client(response_func=BackgroundResponse.fail)
    async def handle_asset_purchase_request_processing(self, request):
        asset_id = request['asset']['id']
        request_id = request['id']
        self.logger.info(
            f"handle_asset_purchase_request_processing {request_id}",
        )
        test_id = await self.db.get_test_id_from_object_id(asset_id)
        await self.db.check_step(test_id, 'purchase', request_id)
        return BackgroundResponse.done()

    @event(
        'asset_adjustment_request_processing',
        statuses=[
            'approved',
        ],
    )
    @safe_client(response_func=BackgroundResponse.fail)
    async def handle_asset_adjustment_request_processing(self, request):
        asset_id = request['asset']['id']
        request_id = request['id']
        self.logger.info(f"handle_asset_adjustment_request_processing {request_id}")
        test_id = await self.db.get_test_id_from_object_id(asset_id)
        await self.db.update_step_object_id(test_id, 'adjustment', request_id)
        await self.db.check_step(test_id, 'adjustment', request_id)
        r = await create_change_request(
            client=self.client,
            product_id=request['asset']['product']['id'],
            request_id=request_id,
            asset_id=asset_id,
        )
        await self.db.add_new_step(asset_id, 'change', r['id'])
        return BackgroundResponse.done()

    @event(
        'asset_change_request_processing',
        statuses=[
            'approved',
        ],
    )
    @safe_client(response_func=BackgroundResponse.fail)
    async def handle_asset_change_request_processing(self, request):
        asset_id = request['asset']['id']
        request_id = request['id']
        self.logger.info(f"handle_asset_change_request_processing {request_id}")
        test_id = await self.db.get_test_id_from_object_id(asset_id)
        await self.db.check_step(test_id, 'change', request_id)
        r = await create_request(
            client=self.client,
            request_type='suspend',
            asset_id=asset_id,
        )
        await self.db.add_new_step(asset_id, 'suspend', r['id'])
        return BackgroundResponse.done()

    @event(
        'asset_suspend_request_processing',
        statuses=[
            'approved',
        ],
    )
    @safe_client(response_func=BackgroundResponse.fail)
    async def handle_asset_suspend_request_processing(self, request):
        asset_id = request['asset']['id']
        request_id = request['id']
        self.logger.info(
            f"handle_asset_suspend_request_processing {request_id}",
        )
        test_id = await self.db.get_test_id_from_object_id(asset_id)
        await self.db.check_step(test_id, 'suspend', request_id)
        r = await create_request(
            client=self.client,
            request_type='resume',
            asset_id=asset_id,
        )
        await self.db.add_new_step(asset_id, 'resume', r['id'])
        return BackgroundResponse.done()

    @event(
        'asset_resume_request_processing',
        statuses=[
            'approved',
        ],
    )
    @safe_client(response_func=BackgroundResponse.fail)
    async def handle_asset_resume_request_processing(self, request):
        asset_id = request['asset']['id']
        request_id = request['id']
        self.logger.info(f"handle_asset_resume_request_processing {request_id}")
        test_id = await self.db.get_test_id_from_object_id(asset_id)
        await self.db.check_step(test_id, 'resume', request_id)
        r = await create_request(
            client=self.client,
            request_type='cancel',
            asset_id=request['asset']['id'],
        )
        await self.db.add_new_step(asset_id, 'cancel', r['id'])
        return BackgroundResponse.done()

    @event(
        'asset_cancel_request_processing',
        statuses=[
            'approved',
        ],
    )
    @safe_client(response_func=BackgroundResponse.fail)
    async def handle_asset_cancel_request_processing(self, request):
        asset_id = request['asset']['id']
        request_id = request['id']
        self.logger.info(f"handle_asset_cancel_request_processing {request_id}")
        test_id = await self.db.get_test_id_from_object_id(asset_id)
        await self.db.check_step(test_id, 'cancel', request_id)
        if (
            len(await self.db.get_steps_to_check(test_id=test_id)) == 0
            and await self.db.get_step_count(test_id=test_id) == 6
        ):
            await self.db.set_test_result(test_id, ResultType.success.value)
        return BackgroundResponse.done()
