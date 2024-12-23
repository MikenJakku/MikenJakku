#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
from core.algorithm_library.WT_Project.wt_direct import WTDirect
from core.algorithm_frame.base_class.monitor_base import MonitorBase


class WT_Direct(MonitorBase):
    def init_algorithm(self):
        """
        初始化算法类
        抽象方法，在子类中必须进行实现。监测对象中应当至少含有一个算法类对象。
        """
        channels = ['ch1', 'ch2', 'ch3', 'ch4', 'ch5', 'ch6', 'ch7', 'ch8', 'ch9', 'ch10', 'ch11', 'ch12']
        for ch in channels:
            config_dict = self.config.__dict__[ch]
            config_dict.update({"crud_instance": self.CRUD})
            self.algorithm_dict[ch] = WTDirect(**config_dict)
