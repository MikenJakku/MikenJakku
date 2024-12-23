#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
import os
from core.algorithm_library.PowerStation.DataReduction import DataRe
from core.algorithm_library.PowerStation.Statistics import Stat
from core.algorithm_library.PowerStation.Diagnosis import Diagnosis


class AbNoise:
    def __init__(self, crud_instance, **algorithm_config):
        self.crud = crud_instance
        for key, val in algorithm_config.items():
            setattr(self, key, val)

    def __update_algorithm_configs(self, equipment_id):
        """
        根据设备和通道更新参数
        """
        self.equipment_id = equipment_id
        self.algorithm_config = self.crud.get_monitor_config(user='algorithm', equipment_id=self.equipment_id).__dict__

        for key, val in self.algorithm_config.items():
            setattr(self, key, val)

        self.savedir = os.path.join(self.crud.database_root, self.equipment_id)

    def rt_diagnosis(self, raw, sr, equipment_id, position):
        """
        对一路声信号进行异常音的诊断。
        :param equipment_id: str, 设备编号
        :param data_pack: dict, 传入数据
        :return: 是否存在异音、异音最大
        """
        self.__update_algorithm_configs(equipment_id)
        self.sr = sr

        dr_tools = DataRe(sr)
        st_tools = Stat(sr, self.window_ENBW)

        configs = self.__dict__
        dg_tools = Diagnosis(configs)

        # 数据预处理；滤去低频干扰和高频谐振部分
        data = dr_tools.butterworth_filter(raw, self.filter_band["low"], self.filter_band["high"],
                                           self.filter_band["order"])

        # 总声压级增加
        OA = st_tools.oa(raw, self.OA_freq_range["high"], self.OA_freq_range["low"])
        OA_status = dg_tools.oa_status(OA)

        # 频谱成分异常
        spec_status = dg_tools.abnormal_noise(data)

        if (OA_status in ["warning", "fatal"]) or spec_status:
            return {"overall": OA_status,
                    "abnormal":spec_status}
