#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====

from importlib import import_module
from core.CRUD_toolkits.CRUD import CRUD


def test_case(monitor_config_name):
    monitor_CRUD = CRUD(monitor_config_name)
    monitor_config = monitor_CRUD.get_monitor_config()
    print("监测对象名称：", monitor_config.monitor_name)
    print("监测对象版本：", monitor_config.monitor_version)

    # 导入监测类，实例化场景对应的算法类
    module = import_module("core.monitor_library." + monitor_config.monitor_name)
    monitor = getattr(module, monitor_config.monitor_class)(config_name=monitor_config_name, user="initializer")

    for algorithm in monitor_config.task_pack:  # 从配置文件中取出算法名
        print("算法类名称：", algorithm)

        algorithm_class = monitor.algorithm_dict[algorithm]
        for task_name in monitor_config.task_pack[algorithm]:
            _ = getattr(algorithm_class, task_name)
            print("接口", task_name, "存在性校验成功！")


if __name__ == "__main__":
    test_case("PD.json")
