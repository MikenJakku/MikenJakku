#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
import numpy
import os
from core.algorithm_library.general_feature_analysis import statistics


class VibThreshold:
    def __init__(self, crud_instance, **configs: dict):
        self.crud = crud_instance

        for key, val in configs.items():
            setattr(self, key, val)

    def __update_configs(self, equipment_id):
        """
        根据设备和通道更新参数
        :param equipment_id: 设备号
        :return: 无
        """
        self.equipment_id = equipment_id
        self.algorithm_config = self.crud.get_monitor_config(user='algorithm', equipment_id=equipment_id).__dict__

        for key, val in self.algorithm_config.items():
            setattr(self, key, val)

        self.savedir = os.path.join(self.crud.database_root, equipment_id)

    def threshold(self, scenario, equipment_id, position, datetime, raw, sample_rate):
        """
        阈值法诊断当前测点数据是否存在振动异常。
        """
        exception_code = None

        if len(equipment_id):
            self.__update_configs(equipment_id)
            
        rms_threshold = self.rms_th[position]
        data = raw
        char_val = statistics.rms(data)

        if char_val > rms_threshold:
            exception_code = "0"

        return {"exception_code": exception_code,
                "characteristic_value": char_val.tolist()}
