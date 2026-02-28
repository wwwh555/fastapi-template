#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter
from app.modules.user.api.v1 import user

v1 = APIRouter()

v1.include_router(user.router, tags=['用户管理'])
