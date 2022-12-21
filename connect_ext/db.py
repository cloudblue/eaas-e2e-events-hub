# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, CloudBlue
# All rights reserved.
#
import asyncio
import sqlite3
from datetime import datetime, timedelta
from typing import List, Tuple

from connect_ext.models import ResultType, Step, TstInstance


DO_NOT_CHECK_AFTER_SECONDS = 120


class DB:

    def __init__(self, database: str = 'data.db'):
        self.connection = sqlite3.connect(database, check_same_thread=False)
        cur = self.connection.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS test("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "running BOOLEAN, "
            "result VARCHAR(255), "
            "object_id VARCHAR(255), "
            "done_at DATETIME, "
            "created_at DATETIME)",
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS step("
            "test_id INTEGER, "
            "name VARCHAR(255), "
            "object_id VARCHAR(255), "
            "created_at DATETIME, "
            "checked BOOLEAN, "
            "checked_at DATETIME)",
        )
        cur.close()

    async def is_idle(self) -> None:
        return await asyncio.get_running_loop().run_in_executor(None, self._is_idle)

    async def get_steps_to_check(self, test_id: int) -> List[Tuple]:
        return await asyncio.get_running_loop().run_in_executor(
            None,
            self._get_steps_to_check,
            test_id,
        )

    async def get_step_count(self, test_id: int) -> int:
        return await asyncio.get_running_loop().run_in_executor(
            None,
            self._get_step_count,
            test_id,
        )

    async def check_step(self, test_id: int, name: str, object_id: str = None) -> None:
        return await asyncio.get_running_loop().run_in_executor(
            None,
            self._check_step,
            test_id,
            name,
            object_id,
        )

    async def add_new_step(self, asset_id: str, name: str, request_id: str = None) -> None:
        return await asyncio.get_running_loop().run_in_executor(
            None,
            self._add_new_step,
            asset_id,
            name,
            request_id,
        )

    async def is_running_a_test(self) -> bool:
        return await asyncio.get_running_loop().run_in_executor(None, self._is_running_a_test)

    async def create_new_test(self, object_id: str) -> TstInstance:
        return await asyncio.get_running_loop().run_in_executor(
            None,
            self._create_new_test,
            object_id,
        )

    async def list_tests(self) -> List[TstInstance]:
        return await asyncio.get_running_loop().run_in_executor(None, self._list_tests)

    async def get_test(self, test_id: int) -> TstInstance:
        return await asyncio.get_running_loop().run_in_executor(None, self._get_test, test_id)

    async def get_test_id_from_object_id(self, object_id: str) -> int:
        return await asyncio.get_running_loop().run_in_executor(
            None,
            self._get_test_id_from_object_id,
            object_id,
        )

    async def set_test_result(self, test_id, result: str = ResultType.success.value) -> None:
        return await asyncio.get_running_loop().run_in_executor(
            None,
            self._set_test_result,
            test_id,
            result,
        )

    async def update_step_object_id(self, test_id: int, name: str, object_id: str) -> None:
        return await asyncio.get_running_loop().run_in_executor(
            None,
            self._update_step_object_id,
            test_id,
            name,
            object_id,
        )

    def _is_idle(self) -> None:
        with self.connection as c:
            res = c.execute('SELECT COUNT(*) FROM test WHERE running is True')
            result = res.fetchone()
            return result[0] == 0

    def _get_steps_to_check(self, test_id: int) -> List[Tuple]:
        with self.connection as c:
            res = c.execute(
                'SELECT object_id, created_at '
                'FROM step '
                'WHERE checked IS False '
                'AND object_id IS NOT NULL '
                'AND test_id=? '
                'AND created_at < ?',
                (test_id, datetime.now() - timedelta(seconds=DO_NOT_CHECK_AFTER_SECONDS)),
            )
            return res.fetchall()

    def _get_step_count(self, test_id: int) -> int:
        with self.connection as c:
            res = c.execute(
                'SELECT COUNT(*) '
                'FROM step '
                f'WHERE test_id={test_id} AND checked is True',
            )
            result = res.fetchone()
            if result:
                return result[0]
            return 0

    def _check_step(self, test_id, name, object_id) -> None:
        with self.connection as c:
            sql = (
                'UPDATE step '
                'SET checked=?, checked_at=? '
                'WHERE test_id=? AND checked is False AND name=?'
            )
            data = (True, datetime.now(), test_id, name)
            if object_id:
                sql += ' AND object_id=?'
                data = data + (object_id,)
            c.execute(
                sql,
                data,
            )

    def _add_new_step(self, asset_id: str, name: str, request_id: str) -> None:
        test_id = self._get_test_id_from_object_id(asset_id)
        now = datetime.now()
        data = (test_id, name, now, False, None)
        sql = (
            'INSERT INTO step(test_id,name,created_at,checked,checked_at) '
            'VALUES(?,?,?,?,?)'
        )
        if request_id:
            sql = (
                'INSERT INTO step(test_id,name,created_at,checked,checked_at,object_id) '
                'VALUES(?,?,?,?,?,?)'
            )
            data = data + (request_id,)
        with self.connection as c:
            c.execute(
                sql,
                data,
            )

    def _is_running_a_test(self) -> bool:
        return not self._is_idle()

    def _create_new_test(self, object_id: str) -> TstInstance:
        if self._is_idle():
            with self.connection as c:
                c.execute(
                    'INSERT INTO test(running,result,object_id,done_at,created_at)'
                    ' VALUES(?,?,?,?,?)',
                    (True, None, object_id, None, datetime.now()),
                )
                tests = self._build_test_objects(sql_filter='running is True')
                return tests[0]

    def _build_test_objects(self, sql_filter: str = None) -> List[TstInstance]:
        with self.connection as c:
            tests = []
            test_cursor = c.execute('SELECT * FROM test')
            if sql_filter:
                test_cursor = c.execute(f'SELECT * FROM test WHERE {sql_filter}')
            for test in test_cursor.fetchall():
                step_cursor = c.execute(f'SELECT * FROM step WHERE test_id = {test[0]}')
                steps = []
                for step in step_cursor.fetchall():
                    d = {
                        step_cursor.description[i][0]: str(step[i])
                        if step[i] else None
                        for i in range(len(step_cursor.description))
                    }
                    steps.append(Step(**d))
                data = {
                    test_cursor.description[i][0]: str(test[i])
                    if test[i] else None
                    for i in range(len(test_cursor.description))
                }
                data['steps'] = steps
                test = TstInstance(**data)
                tests.append(test)
            return tests

    def _list_tests(self) -> List[TstInstance]:
        return self._build_test_objects()

    def _get_test(self, test_id: int) -> TstInstance:
        tests = self._build_test_objects(sql_filter=f'id = "{test_id}"')
        return tests[0] if tests else None

    def _get_test_id_from_object_id(self, object_id: str) -> int:
        with self.connection as c:
            res = c.execute(f'SELECT id FROM test WHERE object_id="{object_id}"')
            data = res.fetchone()
            if data:
                return data[0]
            return None

    def _set_test_result(self, test_id: int, result: str) -> None:
        with self.connection as con:
            con.execute(
                'UPDATE test '
                'SET result=?, done_at=?, running=? '
                f'WHERE done_at IS NULL AND id="{test_id}"',
                (result, datetime.now(), False),
            )

    def _update_step_object_id(self, test_id: int, name: str, object_id: str) -> None:
        with self.connection as con:
            con.execute(
                'UPDATE step '
                'SET object_id=? '
                'WHERE test_id=? AND name=?',
                (object_id, test_id, name),
            )


db = DB()


def get_db():
    return db
