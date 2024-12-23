#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
import os
from core.algorithm_library.PowerStation.SingleBearing import SingleBearing
from core.algorithm_frame.base_class.monitor_base import MonitorBase
import numpy as np
from pprint import pprint


class SingleBearingEquipment(MonitorBase):
    def init_algorithm(self):
        """
        初始化通道类
        抽象方法，在子类中必须进行实现。监测对象中应当至少含有一个通道对象。
        """
        algorithms = 'general'
        config_dict = self.config.__dict__
        config_dict.update({"crud_instance": self.CRUD})
        self.algorithm_dict[algorithms] = SingleBearing(**config_dict)


def test():
    npy_dir = r'D:\DataArchive\gearbox_sample\Download'
    for npyn in os.listdir(npy_dir):
        if npyn.endswith('.npy'):
            raw = np.load(os.path.join(npy_dir, npyn))

            task_pack = {
                'task_type': ["rt_diagnosis"],
                'algorithm_name': "general",
                'data_pack': {
                    'equipment_id': 'Kunshan_turbine_AC_oil_pump',
                    'Ax': {
                        'raw': raw,
                        'rotat_freq': 13.33,
                        'sr': 50000,
                    },
                    'RH': {
                        'raw': raw + np.random.randn(len(raw)),
                        'rotat_freq': 13.33,
                        'sr': 50000,
                    },
                    'RV': {
                        'raw': None,
                        'rotat_freq': 13.33,
                        'sr': 50000,
                    }
                }
            }

            bearing_monitor = SingleBearingEquipment(config_name="Single_Bearing_Equipment.json", user='algorithm')
            result = bearing_monitor.task_processing(task_pack)
            # pprint(result[task_pack['task_type'][0]])
            pprint(result)
            print('\n')


if __name__ == "__main__":
    test()
