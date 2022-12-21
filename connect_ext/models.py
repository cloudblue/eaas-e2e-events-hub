# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, CloudBlue
# All rights reserved.
#
from typing import List, Optional, Union
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, validator


class ResultType(Enum):
    success = 'success'
    failed = 'failed'


class Step(BaseModel):
    test_id: Optional[int]
    name: str
    object_id: Optional[str]
    created_at: datetime
    checked: Optional[bool]
    checked_at: Optional[datetime]

    class Config:
        fields = {'test_id': {'exclude': True}}

    @validator('test_id')
    def validate_test_id(value):
        return value or None

    @validator('checked')
    def validate_checked(value):
        return value or False


class TstInstance(BaseModel):
    id: Optional[int]
    running: Optional[bool]
    result: Optional[Union[ResultType, str]]
    object_id: Optional[str]
    done_at: Optional[datetime]
    created_at: Optional[datetime]
    steps: Optional[List[Step]]

    @validator('running')
    def validate_running(value):
        return value or False

    @validator('result')
    def validate_result(value):
        if isinstance(value, str):
            value = ResultType[value]
        return value or None

    @validator('done_at')
    def validate_done_at(value):
        return value or None


class ErrorResponse(BaseModel):
    detail: str


class TestRequest(BaseModel):
    product_id: str
    hub_id: str
