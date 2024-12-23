#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
from core.algorithm_frame.base_class.monitor_base import MonitorBase
from core.algorithm_library.PowerStation.VibThresholding import VibThreshold

import numpy as np


class Threshold(MonitorBase):
    def init_algorithm(self):
        """
        初始化通道类
        抽象方法，在子类中必须进行实现。监测对象中应当至少含有一个通道对象。
        """
        algorithms = 'general'
        config_dict = self.config.__dict__
        config_dict.update({"crud_instance": self.CRUD})
        self.algorithm_dict[algorithms] = VibThreshold(**config_dict)

    def report(self,task):
        """
        算法返回结果
        {'general': None, 'threshold': {'exception_code': '0', 'characteristic_value': 0.5}}
        0:excessive_vibration
        ValidatingData:abnormal_noises
        """
        print('self.result_dict before report ={}'.format(self.result_dict))
        if self.result_dict['threshold']['exception_code'] is not None:
            self.result_dict['threshold']['exception_code'] = self.config.crud_instance.label_mapping[self.result_dict['threshold']['exception_code']]
        else:
            pass
        print('self.result_dict after report ={}'.format(self.result_dict))
        return self.result_dict

def monitor_example():
    task_pack = {
        "task_type": ["threshold"],
        "algorithm_name": "general",
        "data_pack": {
            "scenario": "Thresholding",
            "equipment_id": "11F",
            "position": "lower_bracket_y",
            "datetime": "2023-12-15-16-00-00",
            "raw": np.random.randn(4800),
            "sample_rate": 96000
        }
    }


    monitor = Threshold(config_name='Thresholding.json')
    result = monitor.task_processing(task_pack)

    print(result)

    return 0


if __name__ == "__main__":
    monitor_example()

