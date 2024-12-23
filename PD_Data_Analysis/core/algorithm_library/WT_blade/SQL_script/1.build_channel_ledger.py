#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
import json
from core.CRUD_toolkits.CRUD import CRUD

"""
构造通道台账表
"""
crud = CRUD()

sql_info = json.load(open("sql_info.json", "r", encoding="utf-8"))
crud.sql_connect(**sql_info)  # 传入数据库信息，用以连接数据库

header_list = ['channel_name', 'collector', 'position', 'equipment', 'part']
data_type_list = ['varchar(10)', 'varchar(10)', 'varchar(10)', 'varchar(10)', 'varchar(10)']
table_name = "channel_ledger"

crud.sql_tools.build_table(table_name=table_name,
                           header_list=header_list,
                           data_type_list=data_type_list)
