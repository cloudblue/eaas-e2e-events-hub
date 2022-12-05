# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, CloudBlue
# All rights reserved.
#
from typing import List, Union
from logging import LoggerAdapter

from fastapi import Depends, status
from fastapi.responses import JSONResponse
from connect.eaas.core.decorators import (
    router,
    web_app,
)
from connect.eaas.core.extension import WebApplicationBase
from connect.eaas.core.inject.common import get_logger
from connect.eaas.core.inject.asynchronous import get_extension_client
from connect.client import AsyncConnectClient

from connect_ext.models import ErrorResponse, ResultType, TestRequest, TstInstance
from connect_ext.decorators import safe_client
from connect_ext.db import get_db
from connect_ext.operations import (
    change_draft_to_pending,
    create_draft_request,
    get_request_by_id,
    validate_request,
)


ERROR_RESPONSE_DICT = {
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        'model': ErrorResponse,
        'description': (
            'Something wrong happened while processing the request. Please try again later'
        ),
    },
    status.HTTP_400_BAD_REQUEST: {'model': ErrorResponse},
    status.HTTP_404_NOT_FOUND: {'model': ErrorResponse},
}


@web_app(router)
class TstWebApplication(WebApplicationBase):

    @router.post(
        '/tests',
        summary="Create and start test",
        description="This endpoint creates a new test. Only 1 test could be run at the same time.",
        status_code=status.HTTP_201_CREATED,
        response_model=Union[TstInstance, ErrorResponse],
        responses=ERROR_RESPONSE_DICT,
    )
    @safe_client()
    async def start_test(
        self,
        request: TestRequest,
        logger: LoggerAdapter = Depends(get_logger),
        db: any = Depends(get_db),
        client: AsyncConnectClient = Depends(get_extension_client),
    ):
        product_id = request.product_id
        hub_id = request.hub_id
        logger.info(f'CLIENT CLASS ->{type(client)}')
        logger.info(f'DB CLASS ->{db}')

        if not await db.is_idle():
            error = {'detail': 'Test still running. Wait a second or call /tests/{id}/check.'}
            logger.info(error)
            return JSONResponse(content=error, status_code=status.HTTP_400_BAD_REQUEST)

        account_id = (await client.accounts.all().first())['id']

        r = await create_draft_request(
            client,
            'production',
            account_id,
            product_id,
            hub_id,
        )
        request_id = r['id']
        logger.info(r)

        r = await get_request_by_id(client, request_id)
        await validate_request(client, r)
        asset_id = r['asset']['id']
        test = await db.create_new_test(object_id=asset_id)
        if not test:
            error = {'detail': 'Test still running.'}
            logger.info(error)
            return JSONResponse(content=error, status_code=status.HTTP_400_BAD_REQUEST)

        await change_draft_to_pending(client, request_id)
        await db.add_new_step(asset_id, 'purchase', r['id'])
        await db.add_new_step(asset_id, 'adjustment')
        test = await db.get_test(test.id)
        return test

    @router.get(
        '/tests',
        summary="List tests",
        description="This endpoint return the test list.",
        response_model=Union[List[TstInstance], ErrorResponse],
        responses=ERROR_RESPONSE_DICT,

    )
    @safe_client()
    async def get_test_list(
        self,
        db: any = Depends(get_db),
        logger: LoggerAdapter = Depends(get_logger),
    ):
        return await db.list_tests()

    @router.get(
        '/tests/{id}',
        summary="Get test",
        description="This endpoint retrieves a test given the id.",
        response_model=Union[TstInstance, ErrorResponse],
        responses=ERROR_RESPONSE_DICT,
    )
    @safe_client()
    async def get_test(
        self,
        id,
        db: any = Depends(get_db),
        logger: LoggerAdapter = Depends(get_logger),
    ):
        test = await db.get_test(id)
        if test:
            return test
        return JSONResponse(
            content={'detail': f'the test with id {id} does not exist'},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    @router.post(
        '/tests/{id}/check',
        summary="Check test",
        description="This endpoint checks manually the test results.",
        response_model=TstInstance,
        responses=ERROR_RESPONSE_DICT,
    )
    @safe_client()
    async def check_test(
        self,
        id,
        db: any = Depends(get_db),
        logger: LoggerAdapter = Depends(get_logger),
        client: AsyncConnectClient = Depends(get_extension_client),
    ):
        test = await db.get_test(id)
        error = None
        status_code = status.HTTP_400_BAD_REQUEST
        if not test:
            error = f'test with id {id} does not exist.'
            status_code = status.HTTP_404_NOT_FOUND
        elif not test.running:
            return test
        else:
            requests = await db.get_steps_to_check(test_id=id)
            logger.info(f'check_request_status {requests}')
            for r in requests:
                logger.info(f'check_request_status {r}')
                request = await get_request_by_id(client, r[0])
                if request['status'] != 'approved':
                    error = (
                        f"The {request['type']} {r[0]} is in {request['status']} "
                        f"status instead of approved.",
                    )
                    break
                else:
                    await db.check_step(id, r[0])

            if not error:
                steps_done = await db.get_step_count(id)
                if steps_done != 6:
                    test = await db.get_test(id)
                    error = f'The step {test.steps[steps_done-1].name} has not finished!'

            logger.info('The check process has been done!!')

        if error:
            await db.set_test_result(id, ResultType.failed.value)
            logger.info(error)
            return JSONResponse(content={'detail': error}, status_code=status_code)
        else:
            await db.set_test_result(id, ResultType.success.value)
            return await db.get_test(id)
