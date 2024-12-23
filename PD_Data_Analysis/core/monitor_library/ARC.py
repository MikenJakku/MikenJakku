from core.algorithm_frame.base_class.monitor_base import MonitorBase

from core.algorithm_library.ARC.predict import SignalClassifier

import numpy as np


class ARCMonitor(MonitorBase):
    def init_algorithm(self, **init_parameter):
        """
        初始化算法类
        抽象方法，在子类中必须进行实现。监测对象中应当至少含有一个算法类对象。
        """
        self.algorithm_dict["general"] = SignalClassifier(self.config)

    def data_exception(self, sr):
        """
        数据异常处理
        """
        if sr != self.config.sr:
            return False
        else:
            return True


def task_test():
    task_pack = {
        'task_type': ["ARC"],
        'algorithm_name': "general",
        'data_pack': {
            'data': np.random.rand(960000),
        }
    }

    example_monitor = ARCMonitor(config_name="ARC.json", user="initializer")
    if example_monitor.data_exception(sr=96000):
        result = example_monitor.task_processing(task=task_pack)
        print(result)
    pass


if __name__ == "__main__":
    task_test()
