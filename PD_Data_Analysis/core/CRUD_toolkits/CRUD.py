#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====

import os
import pickle
import warnings
import json
import datetime
from core.CRUD_toolkits.SQL_toolkits import SQL


class CRUD:
    version = "CRUD_2.4.2.0"
    """
    依赖监测对象配置文件，进行监测对象的配置类管理，负责资源库的交互。
    特性一览：
    ValidatingData、CRUD工具包针对单一监测对象进行资源库的管理，每个监测对象有独立的资源库空间。通过传入监测对象配置文件，CRUD将实现对资源库的管理。
    2、在资源库中，监测对象下辖数据库和设备参数库，通过设备注册机制，在监测对象的空间中，建立设备专属的数据库和设备参数库。
    3、目前设备的参数资源库不支持删除操作，持久化数据可以进行删除操作。
    4、通过get_monitor_config函数，将返回各个用户所需的监测对象配置信息。若指定了设备编号，则返回该设备的参数资源库信息。
    5、资源库的参数更新机制，需要用户实现准备设备ID列表与参数列表，CRUD将根据设备ID列表，更新设备参数库中的参数。
    6、数据持久化通过唯一标识进行存储和读取，若唯一标识已存在，则进行覆盖操作。
    ===========================================================================================================
    2.1新特性：
    (ValidatingData)根据CRUD规定的强制字段检查配置文件，若配置文件不符合规范，则会抛出异常。
    (2)原则上支持了使用配置文件动态调整资源库存储位置。
    (3)修复了设备重复注册时，资源库中设备参数库的重复创建问题。
    2.2新特性：添加了一个时间序列方式存储的数据持久化方法
    2.3新特性：
    数据库清理功能，预计支持删除和归档两种模式。
    删除模式：删除数据的接口效果一致，但会批量删除，无需使用者记录唯一标识。
    归档模式（尚未实现）：会清空存储空间，但会将历史数据移动到其他地方归档保存。
    默认采用删除模式。
    2.4新特性：
    (ValidatingData)新增数据库交互模块，提供了特征建表，特征扩展，特征持久化，时间区间特征查询功能。
    (2)允许CRUD工具包初始化的时候，不传入配置文件就可以直接使用内置工具包。
    2.4.1新特性：尝试修复了json保存中文时，展示错误的问题。
    2.4.2新特性：修复了sql_tools建表时，不指定主键约束时，sql语句错误的问题。
    """

    def __init__(self, config_name=None):
        self.resource_root = None  # 资源库根目录
        self.database_root = None  # 数据库根目录
        self.equipment_root = None  # 设备参数库根目录

        self.monitor_config = None  # 监测对象全部配置

        self.monitor_version = None  # 监测对象版本
        self.monitor_description = None  # 监测对象描述
        self.monitor_name = None  # 监测对象所在文件名
        self.monitor_class = None  # 监测对象类名
        self.task_pack = None  # 任务包格式
        self.init_parameter = None  # 初始化参数
        self.self_define_parameter = None  # 自定义参数
        self.variable_parameter = None  # 可变参数
        self.task_mapping = None  # 任务映射
        self.label_mapping = None  # 标签映射

        self.core_path = os.path.dirname(os.path.dirname(__file__))  # core目录路径
        if config_name is not None:
            self.__load_monitor_config(config_name)
            self.__root_init()

        self.sql_tools = SQL  # 数据库交互工具包

    def sql_connect(self, host, db_name, port=3306, user='', password=''):
        """
        连接数据库接口
        :param host: 数据库服务器地址
        :param db_name: 数据库名
        :param port: 数据库端口
        :param user: 用户名
        :param password: 密码
        """

        if user == '':
            user = input('请输入用户名：')
        if password == '':
            password = input('请输入{}用户密码：'.format(user))

        self.sql_tools = SQL(host=host, port=port, user=user, password=password, db_name=db_name)

    def __root_init(self):
        """
        初始化资源库根目录
        """
        if self.resource_root is None:
            self.resource_root = os.path.join(self.core_path, "resource_library", self.monitor_name)
        if self.database_root is None:
            self.database_root = os.path.join(self.resource_root, "database")
        if self.equipment_root is None:
            self.equipment_root = os.path.join(self.resource_root, "equipment")

        # 若首次运行此实例，则会创建属于这个监测对象的专属资源库空间。
        if not os.path.exists(self.resource_root):
            os.mkdir(self.resource_root)
        if not os.path.exists(self.database_root):
            os.mkdir(self.database_root)
        if not os.path.exists(self.equipment_root):
            os.mkdir(self.equipment_root)

    def __load_monitor_config(self, config_name):
        """
        加载监测对象配置文件
        :param config_name: 配置文件名
        """
        config_json_path = os.path.join(self.core_path, "algorithm_config", config_name)
        with open(config_json_path, "r", encoding="utf-8") as f:
            monitor_config_dict = eval(f.read())
        self.monitor_config = monitor_config_dict

        for key in monitor_config_dict:
            if not hasattr(self, key):
                raise AttributeError("{}属性未知，请检查配置文件！".format(key))
            else:
                setattr(self, key, monitor_config_dict[key])

    def __get_equipment_resource(self, equipment_id):
        """
        获取指定设备的资源库数据
        """
        equipment_resource_json_path = os.path.join(self.equipment_root, equipment_id + ".json")
        with open(equipment_resource_json_path, "r", encoding="utf-8") as f:
            equipment_resource_dict = json.load(f)

        return equipment_resource_dict

    def equipment_register(self, equipment_id):
        """
        设备注册，将设备信息写入设备参数库
        :param equipment_id: 设备ID
        """
        equipment_resource_json_path = os.path.join(self.equipment_root, equipment_id + ".json")
        database_dir = os.path.join(self.database_root, equipment_id)
        # 创建给设备专属的资源库空间
        if os.path.exists(equipment_resource_json_path) or os.path.exists(database_dir):
            warnings.warn("{}设备重复注册！".format(equipment_id))
        else:
            os.mkdir(database_dir)

            # 将可变参数写入设备参数库
            with open(equipment_resource_json_path, "w", encoding="utf-8") as f:
                json.dump(self.variable_parameter, f, indent=4, ensure_ascii=False)

    def __update_one_equipment(self, equipment_id, variable_parameter):
        """
        设备更新，将设备信息写入设备参数库
        :param equipment_id: 设备ID
        :param variable_parameter: 可变参数字典
        """
        equipment_resource_json_path = os.path.join(self.equipment_root, equipment_id + ".json")
        # 检查设备注册情况
        if not os.path.exists(equipment_resource_json_path):
            raise ValueError("设备未注册！")

        # 读取已有的设备参数
        with open(equipment_resource_json_path, "r", encoding="utf-8") as f:
            equipment_resource_dict = json.load(f)

        # 更新设备参数
        equipment_resource_dict.update(variable_parameter)
        with open(equipment_resource_json_path, "w", encoding="utf-8") as f:
            json.dump(equipment_resource_dict, f, indent=4, ensure_ascii=False)

    def resource_update(self, equipment_id_list, resource_list):
        """
        资源更新，将资源写入资源库
        :param equipment_id_list: 设备ID列表
        :param resource_list: 资源列表
        """
        if len(resource_list) != len(equipment_id_list):
            if len(resource_list) == 1:
                for equipment_id in equipment_id_list:
                    self.__update_one_equipment(equipment_id, resource_list[0])
            else:
                raise ValueError("设备ID列表与资源列表长度不匹配！")
        else:
            for equipment_id, resource in zip(equipment_id_list, resource_list):
                self.__update_one_equipment(equipment_id, resource)

    def get_monitor_config(self, user="server", equipment_id=None):
        """
        获取配置文件中的指定信息。
        :param user: 用户类型，server、initializer、algorithm
        :param equipment_id: 设备ID
        :return: 配置类
        """

        class Config:
            pass

        config = Config()  # 通用配置类，以类的形式返回配置参数

        if user == "server":
            config.__dict__ = self.monitor_config
        elif user == "initializer":
            config.__dict__ = self.init_parameter
        elif user == "algorithm":
            algorithm_config_dict = self.self_define_parameter  # 算法自定义配置参数
            if equipment_id is None:
                algorithm_config_dict.update(self.variable_parameter)  # 读取默认可变参数
                config.__dict__ = algorithm_config_dict
            else:
                algorithm_config_dict.update(self.__get_equipment_resource(equipment_id))  # 读取设备专属可变参数
                config.__dict__ = algorithm_config_dict
        else:
            raise ValueError("user参数错误，仅支持server、initializer、algorithm")

        return config

    def data_storage_ordinary(self, equipment_id, identification, data_pack):
        """
        外部接口普通数据持久化函数，将数据写入pkl文件
        :param equipment_id: 设备ID
        :param identification: 数据标识
        :param data_pack: 数据包
        """
        pkl_save_path = os.path.join(self.database_root, equipment_id, identification + ".pkl")
        with open(pkl_save_path, "wb") as f:
            pickle.dump(data_pack, f)

    def data_read_ordinary(self, equipment_id, identification):
        """
        外部接口普通数据读取函数，从pkl文件中读取数据
        :param equipment_id: 设备ID
        :param identification: 数据标识
        :return: 数据包
        """
        pkl_save_path = os.path.join(self.database_root, equipment_id, identification + ".pkl")
        with open(pkl_save_path, "rb") as f:
            data_pack = pickle.load(f)
        return data_pack

    def clear_equipment_data(self, equipment_id, mode="delete"):
        """
        清除当前设备下保存的数据数据
        :param equipment_id: 设备ID
        :param mode: 清除模式，delete：删除模式，archive：移动模式
        """
        equipment_database_dir = os.path.join(self.database_root, equipment_id)
        if os.path.exists(equipment_database_dir):
            if mode == "delete":
                for file_name in os.listdir(equipment_database_dir):
                    file_path = os.path.join(equipment_database_dir, file_name)
                    os.remove(file_path)
            elif mode == "archive":
                # todo:尚未实现
                pass
        else:
            warnings.warn("设备{}不存在！".format(equipment_id))

    def data_delete_ordinary(self, equipment_id, identification):
        """
        外部接口普通数据删除函数，从pkl文件中删除数据
        :param equipment_id: 设备ID
        :param identification: 数据标识
        """
        pkl_save_path = os.path.join(self.database_root, equipment_id, identification + ".pkl")
        if os.path.exists(pkl_save_path):
            os.remove(pkl_save_path)
        else:
            warnings.warn("正在删除不存在的数据！")

    def data_storage_time_series(self, equipment_id, data_pack):
        """
        数据持久化函数
        """
        now_time = datetime.datetime.now()  # 取出当前时间
        date = now_time.strftime("%Y-%m-%d")  # 取出当前日期
        identification = now_time.strftime("%Y-%m-%d-%H-%M-%S-%f")  # 取出当前精确时间
        pkl_path_this_day = os.path.join(self.database_root, equipment_id, date + ".pkl")

        # 将data_pack写入pkl文件，若pkl文件不存在则创建。若存在，则将data_pack添加到pkl文件中
        if os.path.exists(pkl_path_this_day):
            with open(pkl_path_this_day, "rb") as f:
                data_pack_old = pickle.load(f)
            data_pack_old[identification] = data_pack
            with open(pkl_path_this_day, "wb") as f:
                pickle.dump(data_pack_old, f)
        else:
            data_pack_new = {identification: data_pack}
            with open(pkl_path_this_day, "wb") as f:
                pickle.dump(data_pack_new, f)

    def data_read_time_series(self, equipment_id, identification):
        """
        数据读取函数
        """
        data_pack_path_this_day = os.path.join(self.database_root, equipment_id,
                                               datetime.datetime.now().strftime("%Y-%m-%d") + ".pkl")

        with open(data_pack_path_this_day, "rb") as f:
            data_pack = pickle.load(f)
        print(len(data_pack))
        return data_pack[identification]
