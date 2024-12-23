#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
"""
删除数据库中所有表
"""
import json
from core.CRUD_toolkits.CRUD import CRUD

crud = CRUD()
sql_info = json.load(open("sql_info.json", "r", encoding="utf-8"))
crud.sql_connect(**sql_info)  # 传入数据库信息，用以连接数据库

crud.sql_tools.drop_all_tables()
