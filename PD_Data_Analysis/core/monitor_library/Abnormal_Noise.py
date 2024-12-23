#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
from core.algorithm_library.PowerStation.AbNoise import AbNoise
from core.algorithm_frame.base_class.monitor_base import MonitorBase
import soundfile as sf


class AbnormalNoise(MonitorBase):
    def init_algorithm(self):
        """
        初始化通道类
        抽象方法，在子类中必须进行实现。监测对象中应当至少含有一个通道对象。
        """
        algorithms = 'general'
        config_dict = self.config.__dict__
        config_dict.update({"crud_instance": self.CRUD})
        self.algorithm_dict[algorithms] = AbNoise(**config_dict)


def test():
    raw_pth = r'D:\DataArchive\WT_blade\defect\P10052-2023-09-28-09-06-40.wav'
    raw, sr = sf.read(raw_pth)

    task_pack = {
        'task_type': ["rt_diagnosis"],
        'algorithm_name': "general",
        'data_pack': {
            'raw': raw,
            'sr': sr,
            'equipment_id': 'Goldwind_test_blade',
            'position': 'axial'
        }
    }

    monitor = AbnormalNoise(config_name="Abnormal_Noise.json", user='algorithm')
    result = monitor.task_processing(task_pack)
    print(result)
    print('\n')


if __name__ == "__main__":
    test()
