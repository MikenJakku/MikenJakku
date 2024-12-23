#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
import json
from core.CRUD_toolkits.CRUD import CRUD
"""
构造时间-BER表脚本
"""
crud = CRUD()
sql_info = json.load(open("sql_info.json", "r", encoding="utf-8"))
crud.sql_connect(**sql_info)

# sql语句，查询channel_ledger表中的所有的channel_name
sql = "SELECT channel_name, collector FROM channel_ledger"
query_info = crud.sql_tools.query_statement_execution(sql)

header_list = ['time', 'ber']
header_type_list = ['datetime', 'varchar(3600)']
for info in query_info:
    table_name = info[1] + "_" + info[0]
    print(table_name)
    header_list = ['time', 'ber']
    crud.sql_tools.build_table(table_name, header_list, header_type_list, primary_key='time')
