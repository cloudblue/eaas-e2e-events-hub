# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, CloudBlue
# All rights reserved.
#
from datetime import datetime

from connect.client import ClientError

from connect_ext.webapp import TstWebApplication
from connect_ext.models import TstInstance


def test_start_test(mocker, test_client_factory, async_client_mocker_factory):
    client = test_client_factory(TstWebApplication)
    client_mocker = async_client_mocker_factory()
    client_mocker.accounts.all().first().mock(return_value=[{'id': 'VA-123-123'}])
    mocker.patch('connect_ext.webapp.create_draft_request', return_value={'id': 'PR-123'})
    mocker.patch(
        'connect_ext.webapp.get_request_by_id',
        return_value={'id': 'PR-123', 'asset': {'id': 'AS-123'}},
    )
    mocker.patch('connect_ext.webapp.validate_request')
    mocker.patch('connect_ext.webapp.change_draft_to_pending')

    body = {
        'product_id': 'PRD-123',
        'hub_id': 'HUB-123',
    }
    client = test_client_factory(TstWebApplication)
    response = client.post(
        '/api/tests',
        json=body,
    )
    assert response.status_code == 201
    test = response.json()
    assert test['id'] == 1
    assert test['running'] is True
    assert test['result'] is None
    assert test['object_id'] == 'AS-123'
    assert test['done_at'] is None
    assert test['created_at'] is not None
    assert len(test['steps']) == 2
    assert test['steps'][0]['name'] == 'purchase'
    assert test['steps'][0]['checked'] is False
    assert test['steps'][1]['name'] == 'adjustment'
    assert test['steps'][1]['checked'] is False


def test_start_test_not_idle(mocker, test_client_factory, async_client_mocker_factory, db):
    client = test_client_factory(TstWebApplication)
    client_mocker = async_client_mocker_factory()
    client_mocker.accounts.all().first().mock(return_value=[{'id': 'VA-123-123'}])
    db.is_idle = mocker.AsyncMock(return_value=False)

    client = test_client_factory(TstWebApplication)
    response = client.post(
        '/api/tests',
        json={
            'product_id': 'PRD-123',
            'hub_id': 'HUB-123',
        },
    )
    assert response.status_code == 400
    assert response.json() == {
        'detail': 'Test still running. Wait a second or call /tests/{id}/check.',
    }


def test_start_test_while_other_already_started(
    mocker,
    test_client_factory,
    async_client_mocker_factory,
    db,
):
    client = test_client_factory(TstWebApplication)
    client_mocker = async_client_mocker_factory()
    client_mocker.accounts.all().first().mock(return_value=[{'id': 'VA-123-123'}])
    mocker.patch('connect_ext.webapp.create_draft_request', return_value={'id': 'PR-123'})
    mocker.patch(
        'connect_ext.webapp.get_request_by_id',
        return_value={'id': 'PR-123', 'asset': {'id': 'AS-123'}},
    )
    mocker.patch('connect_ext.webapp.validate_request')
    mocker.patch('connect_ext.webapp.change_draft_to_pending')
    db.create_new_test = mocker.AsyncMock(return_value=None)

    client = test_client_factory(TstWebApplication)
    response = client.post(
        '/api/tests',
        json={
            'product_id': 'PRD-123',
            'hub_id': 'HUB-123',
        },
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Test still running.'}


def test_list_tests_empty(test_client_factory):

    client = test_client_factory(TstWebApplication)
    response = client.get(
        '/api/tests',
    )
    assert response.status_code == 200
    assert response.json() == []


def test_list_tests_with_connect_error(test_client_factory, mocker):
    mocked_db = mocker.MagicMock()
    mocked_db.list_tests.side_effect = ClientError()
    mocker.patch('connect_ext.db.db', mocked_db)
    client = test_client_factory(TstWebApplication)
    response = client.get(
        '/api/tests',
    )
    assert response.status_code == 400


def test_get_test_not_found(test_client_factory):

    client = test_client_factory(TstWebApplication)
    response = client.get(
        '/api/tests/123',
    )
    assert response.status_code == 404
    assert response.json() == {'detail': 'the test with id 123 does not exist'}


def test_get_and_list_test(test_client_factory, mocker, async_client_mocker_factory):
    client = test_client_factory(TstWebApplication)
    client_mocker = async_client_mocker_factory()
    client_mocker.accounts.all().first().mock(return_value=[{'id': 'VA-123-123'}])
    mocker.patch('connect_ext.webapp.create_draft_request', return_value={'id': '1'})
    mocker.patch(
        'connect_ext.webapp.get_request_by_id',
        return_value={'id': 'PR-123', 'asset': {'id': 'AS-123'}},
    )
    mocker.patch('connect_ext.webapp.validate_request')
    mocker.patch('connect_ext.webapp.change_draft_to_pending')

    response = client.post(
        '/api/tests',
        json={
            'product_id': 'PRD-123',
            'hub_id': 'HB-123',
        },
    )
    assert response.status_code == 201
    test = response.json()
    response = client.get(
        f'/api/tests/{test["id"]}',
    )
    assert response.status_code == 200
    assert response.json() == test

    response = client.get(
        '/api/tests',
    )
    assert response.status_code == 200
    assert response.json() == [test]


def test_check_test_not_found(test_client_factory):
    client = test_client_factory(TstWebApplication)
    response = client.post(
        '/api/tests/33333/check',
    )
    assert response.status_code == 404
    assert response.json() == {'detail': 'test with id 33333 does not exist.'}


def test_check_test_not_running(mocker, test_client_factory, db):
    client = test_client_factory(TstWebApplication)
    db.get_test = mocker.AsyncMock(
        return_value=TstInstance(
            id=1,
            running=False,
            result='success',
            object_id='AS-123',
            created_at=datetime.now(),
            done_at=datetime.now(),
            steps=[],
        ),
    )
    response = client.post(
        '/api/tests/1/check',
    )
    assert response.status_code == 200
    response_test = response.json()
    assert response_test['id'] == 1
    assert response_test['running'] is False
    assert response_test['result'] == 'success'
    assert response_test['object_id'] == 'AS-123'


def test_check_test(mocker, test_client_factory, db):
    client = test_client_factory(TstWebApplication)
    test = TstInstance(
        id=1,
        running=True,
        result=None,
        object_id='AS-123',
        created_at=datetime.now(),
        done_at=None,
        steps=[],
    )
    test2 = TstInstance(
        id=1,
        running=False,
        result='success',
        object_id='AS-123',
        created_at=datetime.now(),
        done_at=datetime.now(),
        steps=[],
    )
    db.get_test = mocker.AsyncMock(
        side_effect=[test, test2],
    )
    db.get_steps_to_check = mocker.AsyncMock(
        return_value=[('PR-123',)],
    )
    db.check_step = mocker.AsyncMock()
    db.get_step_count = mocker.AsyncMock(return_value=6)
    db.set_test_result = mocker.AsyncMock()
    mocker.patch(
        'connect_ext.webapp.get_request_by_id',
        return_value={
            'id': 'PR-123',
            'type': 'purchase',
            'status': 'approved',
        },
    )
    response = client.post(
        '/api/tests/1/check',
    )
    assert response.status_code == 200
    response_test = response.json()
    assert response_test['id'] == 1
    assert response_test['running'] is False
    assert response_test['result'] == 'success'
    assert response_test['object_id'] == 'AS-123'


def test_full_flow(mocker, test_client_factory, async_client_mocker_factory, db):
    client = test_client_factory(TstWebApplication)
    client_mocker = async_client_mocker_factory()
    client_mocker.accounts.all().first().mock(return_value=[{'id': 'VA-123-123'}])
    mocker.patch('connect_ext.webapp.create_draft_request', return_value={'id': '1'})
    mocker.patch(
        'connect_ext.webapp.get_request_by_id',
        return_value={'id': 'PR-123-001', 'asset': {'id': 'AS-123'}},
    )
    mocker.patch('connect_ext.webapp.validate_request')
    mocker.patch('connect_ext.webapp.change_draft_to_pending')

    response = client.post(
        '/api/tests',
        json={
            'product_id': 'PRD-123',
            'hub_id': 'HB-123',
        },
    )
    assert response.status_code == 201
    test = response.json()

    db._add_new_step('AS-123', 'change', 'PR-123-003')
    db._add_new_step('AS-123', 'suspend', 'PR-123-004')
    db._add_new_step('AS-123', 'resume', 'PR-123-005')
    db._add_new_step('AS-123', 'cancel', 'PR-123-006')
    db._update_step_object_id(
        test_id=test['id'],
        name='adjustment',
        object_id='PR-123-002',
    )
    db._check_step(test_id=test['id'], name='purchase', object_id='PR-123-001')
    db._check_step(
        test_id=test['id'],
        name='adjustment',
        object_id='PR-123-002',
    )
    db._check_step(
        test_id=test['id'],
        name='change',
        object_id='PR-123-003',
    )
    db._check_step(test_id=test['id'], name='suspend', object_id='PR-123-004')
    db._check_step(test_id=test['id'], name='resume', object_id='PR-123-005')
    db._check_step(test_id=test['id'], name='cancel', object_id='PR-123-006')

    mocker.patch(
        'connect_ext.webapp.get_request_by_id',
        return_value={
            'id': 'PR-123',
            'type': 'purchase',
            'status': 'approved',
        },
    )
    response = client.post(
        f'/api/tests/{test["id"]}/check',
    )
    assert response.status_code == 200
    response_test = response.json()
    assert response_test['id'] == test['id']
    assert response_test['running'] is False
    assert response_test['result'] == 'success'
    assert response_test['object_id'] == 'AS-123'
    assert len(response_test['steps']) == 6
