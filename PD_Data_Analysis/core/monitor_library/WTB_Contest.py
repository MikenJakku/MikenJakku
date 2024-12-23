#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
import time
from core.algorithm_frame.base_class.monitor_base import MonitorBase
from core.algorithm_library.WTB_contest.WTB_contest import WTBDefect


class WTBContest(MonitorBase):
    def init_algorithm(self):
        """
        初始化算法类
        抽象方法，在子类中必须进行实现。监测对象中应当至少含有一个算法类对象。
        """
        self.config.__dict__.update({"crud_instance": self.CRUD})  # CRUD工具包更新传递
        self.algorithm_dict["general"] = WTBDefect(**self.config.__dict__)

    def data_exception(self, sr, raw):
        """
        外部接口:提供调用层数据异常判断的方法，子类可重写，返回约定的行为
        此方法不是必须实现的，默认返回True
        """
        if len(raw) / sr >= 10:
            return True
        else:
            return False


def task_test():
    import os
    import soundfile as sf
    from matplotlib import pyplot as plt
    from datetime import datetime

    data_dir = r"\\192.168.3.80\算法\声纹-算法\叶片数据\故障叶片1\5ValidatingData"
    wav_name_list = [
        'P10051-2023-10-17-17-21-23.wav',
        'P10051-2023-10-21-10-44-49.wav',
        'P10051-2023-10-21-10-55-51.wav',
        'P10051-2023-10-18-09-42-50.wav',
        'P10051-2023-10-22-10-08-51.wav',
        'P10051-2023-10-25-04-28-53.wav',
        'P10051-2023-09-28-09-06-55.wav',
        'P10051-2023-10-18-00-12-36.wav',
        'P10051-2023-10-25-08-14-26.wav',
        'P10051-2023-09-28-09-21-55.wav',
        'P10051-2023-10-18-06-40-28.wav',
        'P10051-2023-10-18-20-31-16.wav'
    ]

    monitor = WTBContest(config_name="WTB_Contest.json", user="algorithm")

    for wav in wav_name_list:
        wav_path = os.path.join(data_dir, wav)
        raw, sr = sf.read(wav_path)

        date_now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")

        task_pack = {
            'task_type': ["rt_diagnosis"],
            'algorithm_name': "general",
            'data_pack': {
                'raw': raw,
                "sr": sr,
                "dt": date_now,
                "equipment_id": "GoldWind_Contest_Blade",
                "position": "P51"
            }
        }

        result = monitor.task_processing(task=task_pack)

        print(result["rt_diagnosis"])

    return


if __name__ == "__main__":
    task_test()
