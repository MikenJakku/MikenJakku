#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
import os
from core.algorithm_library.PowerStation.GearSystem import Gears
from core.algorithm_frame.base_class.monitor_base import MonitorBase
import numpy as np
from pprint import pprint


class GearSystem(MonitorBase):
    def init_algorithm(self):
        """
        初始化通道类
        抽象方法，在子类中必须进行实现。监测对象中应当至少含有一个通道对象。
        """
        algorithms = 'general'
        config_dict = self.config.__dict__
        config_dict.update({"crud_instance": self.CRUD})
        self.algorithm_dict[algorithms] = Gears(**config_dict)


def test():
    npy_dir = r'D:\DataArchive\gearbox_sample\Download'
    for npyn in os.listdir(npy_dir):
        if npyn.endswith('.npy'):
            raw = np.load(os.path.join(npy_dir, npyn))

            task_pack = {
                'task_type': ["rt_diagnosis"],
                'algorithm_name': "general",
                'data_pack': {
                    "position": "low_end",
                    'equipment_id': 'Test',
                    'raw': raw,
                    'rotat_freq': 13.33,
                    'sr': 50000,

                }
            }

            monitor = GearSystem(config_name="Gear_System.json", user='initializer')
            result = monitor.task_processing(task_pack)
            pprint(result)
            # pprint(result[task_pack['task_type'][0]])
            print('\n')


if __name__ == "__main__":
    test()
