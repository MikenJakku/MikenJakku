from core.algorithm_frame.base_class.monitor_base import MonitorBase

from core.algorithm_library.BYQ.BYQ_class import BYQClass


class BYQMonitor(MonitorBase):
    def init_algorithm(self):
        """
        初始化算法类
        抽象方法，在子类中必须进行实现。监测对象中应当至少含有一个算法类对象。
        """
        self.algorithm_dict["general"] = BYQClass()


def task_test():
    """
    任务包测试用例
    """

    import soundfile as sf
    from matplotlib import pyplot as plt

    data, sr = sf.read(
        r"C:\PyCharmProjecs\sound_data\BYQ\yancheng_zlpc_5.wav")

    task_pack = {
        'task_type': ["real_time_BYQ_anomaly_detection"],
        'algorithm_name': "general",
        'data_pack':
            {
                "sample_rate": sr,
                'data': data,
            }
    }

    byq_monitor = BYQMonitor(config_name="BYQ.json")
    result = byq_monitor.task_processing(task=task_pack)
    print(result)
    pass


if __name__ == "__main__":
    task_test()
