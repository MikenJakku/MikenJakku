#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
import numpy as np
import os
from core.CRUD_toolkits import time_toolkits
from core.algorithm_library.WTB_contest.reduction_statistics import DataPreparation
from core.algorithm_library.WTB_contest.diagnosis import Diagnosis
import pandas as pd


class WTBDefect:
    def __init__(self, crud_instance, **algorithm_config):
        self.crud = crud_instance
        for key, val in algorithm_config.items():
            setattr(self, key, val)

    def __update_algorithm_configs(self, equipment_id: str):
        """
        根据设备和通道更新参数
        :param equipment_id: 设备号
        :return: 无
        """
        self.equipment_id = equipment_id
        self.algorithm_config = self.crud.get_monitor_config(user='algorithm', equipment_id=equipment_id).__dict__

        for key, val in self.algorithm_config.items():
            setattr(self, key, val)

        self.save_dir = os.path.join(self.crud.database_root, equipment_id)

    def __update_position_configs(self, position_datapack: dict):
        """
        读入data_pack中的测点参数
        """
        self.position_cfg = position_datapack
        for key, val in position_datapack.items():
            if key != 'raw':
                setattr(self, key, val)
            else:
                pass

    def rt_diagnosis(self, **data_pack):
        """
        疲劳测试异常检测
        :param data_pack:数据包
        :return:
        """
        equipment_id = data_pack["equipment_id"]
        self.__update_algorithm_configs(equipment_id)
        self.__update_position_configs(data_pack)

        raw = data_pack["raw"]

        configs = self.__dict__
        dp_tools = DataPreparation(configs)
        diag = Diagnosis(configs)

        data = dp_tools.data_reduction(raw)
        result = diag.defect_detection(data)

        jd = round(time_toolkits.date2jd(data_pack["dt"]), 6)

        save_pth = os.path.join(self.save_dir, self.position + '_.csv')
        if os.path.exists(save_pth):
            df = pd.read_csv(save_pth, index_col=0)
            df.loc[jd] = {"status": result["status"],
                          "iBER": result["iBER"],
                          "pp_ratio": result["pp_ratio"],
                          "rms": result["rms"]}
            df.to_csv(save_pth)
        else:
            df = pd.DataFrame([[result["status"], result["iBER"],
                               result["pp_ratio"], result["rms"]]], index=[jd],
                              columns=["status", "iBER", "pp_ratio", "rms"])
            df.to_csv(save_pth)

        return result
