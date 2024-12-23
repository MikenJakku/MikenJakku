#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====

import pymysql


class SQL(object):
    def __init__(self, host, port: int, user, password, db_name):
        """
        sql数据库工具初始化
        :param host 数据库网络地址
        :param port 数据库端口
        :param user 用户名
        :param password 密码
        :param db_name 数据库名
        """

        self.database = pymysql.connect(host=host,
                                        user=user,
                                        password=password,
                                        database=db_name,
                                        port=port
                                        )
        print('数据库{}连接成功！'.format(db_name))
        self.db_cursor = self.database.cursor()

    def build_database(self, db_name: str):
        """
        创建数据库
        :param db_name: 数据库名
        """
        sql = "CREATE DATABASE {}".format(db_name)
        self.db_cursor.execute(sql)
        print('数据库{}创建成功！'.format(db_name))

    def query_info_time(self, table_name: str, header_list: list, time_start, time_end):
        """
        数据查询函数
        :param table_name: 表名字
        :param header_list: 表头列表
        :param time_start: 起始时间
        :param time_end: 结束时间
        :return: 查询结果
        """

        if len(header_list) == 0:
            header_str = "*"
        else:
            header_str = ''
            for i in header_list:
                header_str += i + ','
            header_str = header_str[:-1]

        sql = "SELECT {} FROM {} WHERE time BETWEEN '{}' AND '{}'".format(header_str, table_name, time_start, time_end)
        self.db_cursor.execute(sql)
        result = self.db_cursor.fetchall()
        return result

    def add_header(self, table_name: str, header_name: str, data_type: str):
        """
        添加表头
        :param table_name: 表名字
        :param header_name: 表头名字
        :param data_type: 数据类型
        """

        sql = "ALTER TABLE {} ADD {} {}".format(table_name, header_name, data_type)
        self.db_cursor.execute(sql)
        self.database.commit()
        print('表头{}添加成功！'.format(header_name))

    def add_info(self, table_name: str, value_list: list, header_list=None):
        """
        数据插入函数
        :param table_name: 表名字
        :param value_list: 插入值列表
        :param header_list: 表头列表
        """

        value_str = ''
        for i in value_list:
            value_str += "'" + str(i) + "'" + ','
        if header_list is None:
            sql = "INSERT INTO {} VALUES ({})".format(table_name, value_str[:-1])
        else:
            header_str = ''
            for i in header_list:
                header_str += i + ','
            header_str = header_str[:-1]
            sql = "INSERT INTO {} ({}) VALUES ({})".format(table_name, header_str, value_str[:-1])

        self.db_cursor.execute(sql)
        self.database.commit()

    def build_table(self, table_name: str, header_list: list, data_type_list: list, primary_key=None):
        """
        根据提供的表名，表头列表，数据类型列表，进行建表。
        :param table_name: 表名
        :param header_list: 表头列表
        :param data_type_list: 数据类型列表
        :param primary_key: 主键
        """

        header_str = ''
        for i in header_list:
            header_str += i + ' ' + data_type_list[header_list.index(i)] + ','

        if primary_key is not None:
            header_str += 'PRIMARY KEY ({})'.format(primary_key)
        else:
            header_str = header_str[:-1]

        sql = "CREATE TABLE {} ({})".format(table_name, header_str)
        self.db_cursor.execute(sql)
        self.database.commit()
        print('表{}创建成功！'.format(table_name))

    def drop_table(self, table_name: str):
        """
        删除表
        :param table_name: 表名
        """
        sql = "DROP TABLE {}".format(table_name)
        self.db_cursor.execute(sql)
        self.database.commit()
        print('表{}删除成功！'.format(table_name))

    def query_statement_execution(self, sql: str):
        """
        执行自定义查询语句，可返回结果
        :param sql sql自定义语句
        :return result 查询结果
        """
        self.db_cursor.execute(sql)
        result = self.db_cursor.fetchall()
        return result

    def self_define_statement_execution(self, sql: str):
        """
        执行自定义语句，无需返回结果
        :param sql sql自定义语句
        """
        self.db_cursor.execute(sql)
        self.database.commit()
