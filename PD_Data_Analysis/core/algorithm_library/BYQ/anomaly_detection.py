#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====

import numpy as np
from .config import transformer_config


class AnomalyDetection(object):
    """异常检测类"""

    def __init__(self):
        """初始化参数"""
        self.fault_type = transformer_config.fault_type  # 异常类型
        self.thresh_alarm = transformer_config.thresh_alarm  # 异常数据占比的阈值，用于长时（天、月、年）报警，输入多段数据的特征，计算异常出现的频率，与此阈值比较

    def forward(self, **data_pac: dict) -> dict:
        """
        执行函数，根据特征及特征值，返回异常类型
        :param data_pac: 输入字典：特征及特征值
        :return:异常类型
        """
        result_code = 0
        detection_dict = self.forward_dict(**data_pac)  # 得到各个异常的判断结果
        # print(result_dict)
        for feature, value in detection_dict.items():  # 遍历各个异常的判断结果，给出综合判断
            if value:
                result_code += self.fault_type[feature]['fault_code']
        return {'result': min(result_code, self.fault_type['normal_vibra_ratio']['fault_code'])}

    def forward_dict(self, **data_pac) -> dict:
        """
        根据特征及特征值，返回各个异常的判断结果
        :param data_pac:输入字典：特征及特征值
        :return:各个异常的判断结果
        """
        detection_dict = {}
        for feature, data in data_pac.items():  # 遍历各个特征，调用对应的函数进行判断，给出判断结果
            if feature in self.fault_type.keys():
                detection_dict[feature] = getattr(self, '_' + feature + '_comparison')(feature, data)
        return detection_dict

    def _odd_even_ratio_comparison(self, feature, data) -> bool:
        """
        判断奇偶次谐波比是否正常，与阈值相比
        :param feature:特征名
        :param data:特征值
        :return:是否存在直流偏磁
        """
        data = np.array(data)
        threshold = self.fault_type[feature]['threshold']
        result = np.zeros_like(data)
        result[data > threshold] = 1
        if np.mean(result) > self.thresh_alarm:
            return True
        else:
            return False

    def _base_freq_ratio_comparison(self, feature, data) -> bool:
        """
        判断基频占比是否正常，与阈值相比
        :param feature:特征名
        :param data:特征值
        :return:是否存在重过载
        """
        data = np.array(data)
        threshold = self.fault_type[feature]['threshold']
        result = np.zeros_like(data)
        result[data > threshold] = 1
        if np.mean(result) > self.thresh_alarm:
            return True
        else:
            return False

    def _vibration_entropy_comparison(self, feature, data) -> bool:
        """
        判断振动熵是否正常，与阈值相比
        :param feature:特征名
        :param data:特征值
        :return:是否存在绕组变形/组部件松动
        """
        data = np.array(data)
        threshold = self.fault_type[feature]['threshold']
        result = np.zeros_like(data)
        result[data > threshold] = 1
        if np.mean(result) > self.thresh_alarm:
            return True
        else:
            return False

    def _normal_vibra_ratio_comparison(self, feature, data) -> bool:
        """
        判断振动能量比是否正常，与阈值相比
        :param feature:特征名
        :param data:特征值
        :return:是否能用于变压器诊断
        """
        data = np.array(data)
        threshold = self.fault_type[feature]['threshold']
        result = np.zeros_like(data)
        result[data < threshold] = 1
        if np.mean(result) > self.thresh_alarm:
            return True
        else:
            return False
        pass

    def _main_freq_ratio_comparison(self, feature, data) -> bool:
        """
        判断主频占比是否正常，与阈值相比
        :param feature:特征名
        :param data:特征值
        :return:是否存在铁心故障
        """
        data = np.array(data)
        threshold = self.fault_type[feature]['threshold']
        result = np.zeros_like(data)
        result[data < threshold] = 1
        if np.mean(result) > self.thresh_alarm:
            return True
        else:
            return False
        pass
