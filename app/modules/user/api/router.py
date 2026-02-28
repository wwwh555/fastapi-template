#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter
from app.modules.user.api.user import router

user_router = APIRouter(prefix='/user')

user_router.include_router(router, tags=['用户管理'])