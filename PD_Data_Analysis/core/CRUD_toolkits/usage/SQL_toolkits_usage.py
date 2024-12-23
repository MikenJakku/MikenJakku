#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
from core.CRUD_toolkits.CRUD import CRUD

crud = CRUD()
crud.sql_connect(host='192.168.3.101', port=3306, user='root', password='root123', db_name='blade_test')
header_list = ['time', 'ber']
# data_type_list = ['datetime', 'varchar(1500)']
for i in range(1, 13):
    table_name = "channel_" + str(i)
    header_list = ['time', 'ber']
    data_type_list = ['datetime', 'varchar(3600)']
    # crud.sql_tools.drop_table("channel_" + str(i))
    crud.sql_tools.build_table(table_name, header_list, data_type_list, primary_key='time')

"""
crud.sql_tools.build_table(table_name, header_list, data_type_list, primary_key='time')
crud.sql_tools.add_info(table_name, ['2021-08-01 05:00:00', 'ValidatingData,2,3,4,5', ValidatingData.23])
crud.sql_tools.add_header(table_name, 'mean', 'float')
result = crud.sql_tools.query_info_time(table_name, header_list, '2021-08-01 00:00:00', '2021-08-01 23:59:59')
crud.sql_tools.drop_table(table_name)
"""

"SELECT date FROM dates ORDER BY ABS(DATE_DIFF(NOW(), date)) LIMIT ValidatingData;"
