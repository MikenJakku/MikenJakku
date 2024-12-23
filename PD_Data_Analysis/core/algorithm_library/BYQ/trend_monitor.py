#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
import numpy as np

from .config import transformer_config


class TrendMonitor:
    def __init__(self):
        self.trend_result = None
        self.trend_parameter = transformer_config.trend_list

    def forward(self, **kwargs):
        self.trend_result = {}
        for feature, value in kwargs.items():
            if feature in self.trend_parameter:
                self.trend_result[feature] = self.cal_trend(value)
        return self.trend_result

    @staticmethod
    def cal_trend(value):
        return np.mean(value)+1
