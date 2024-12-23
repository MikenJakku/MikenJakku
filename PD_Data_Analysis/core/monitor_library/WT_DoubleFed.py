#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
from core.algorithm_library.WT_Project.wt_double import WTDouble
from core.algorithm_frame.base_class.monitor_base import MonitorBase
import numpy as np


class WT_DoubleFed(MonitorBase):
    def init_algorithm(self):
        """
        初始化算法类
        抽象方法，在子类中必须进行实现。监测对象中应当至少含有一个算法类对象。
        """
        channels = ['ch1', 'ch2', 'ch3', 'ch4', 'ch5', 'ch6', 'ch7', 'ch8', 'ch9', 'ch10', 'ch11', 'ch12']
        for ch in channels:
            config_dict = self.config.__dict__[ch]
            config_dict.update({"crud_instance": self.CRUD})
            self.algorithm_dict[ch] = WTDouble(**config_dict)


def test():
    # rt_features test
    task_pack = {
        'task_type': ["rt_features"],
        'channel_name': "ch1",
        'data_pack': {
            "raw": np.load(r"D:\DataArchive\风机大唐\test\vib_test.npy"),
            "freq_rpm_high": np.random.randn(9)+37,
            "freq_rpm_low": np.zeros(9),
            "datetime": "20230706120000",
            "equipment_id": "short_test",
            "channel_name": "ch1",
            "sr": 51200}
        }

    print(task_pack["data_pack"]["raw"].shape)

    # # diagnosis_report test
    # task_pack = {
    #     'task_type': ["diagnosis_report"],
    #     'channel_name': "ch1",
    #     'data_pack': {
    #         "datetime": "20230706120000",
    #         "equipment_id": "wt_double_Datang_Habahe",
    #         "channel_name": "ch1",
    #         "sr": 51200}
    #     }

    wt_monitor = WT_DoubleFed(config_name="WT_DoubleFed.json", user='algorithm')
    result = wt_monitor.task_processing(task_pack)
    print(result)

    return None


if __name__=="__main__":
    test()
