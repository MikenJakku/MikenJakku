from core.algorithm_frame.base_class.monitor_base import MonitorBase
from core.algorithm_library.WT_blade.blade_anomaly_detection import BladeDetection


class WtBlade(MonitorBase):
    def init_algorithm(self):
        """
        初始化算法类
        抽象方法，在子类中必须进行实现。监测对象中应当至少含有一个算法类对象。
        """
        self.config.__dict__.update({"crud": self.CRUD})  # CRUD工具包更新传递
        self.algorithm_dict["general"] = BladeDetection(**self.config.__dict__)


def task_test():
    import os
    import soundfile as sf
    from matplotlib import pyplot as plt

    data_dir = r"E:\叶片检测"
    wav_path = os.path.join(data_dir, "P10051-2023-10-10-17-13-04.wav")
    # wav_path = os.path.join(data_dir, "P10051_2023-09-07_00-00-29.wav")
    data_org, sr = sf.read(wav_path)
    # 降采样一半
    data_org = data_org[::2]

    pd_monitor = BladeJF(config_name="WT_blade.json", user="initializer")

    task_pack = {
        'task_type': ["blade_detect"],
        'algorithm_name': "general",
        'data_pack': {
            'data': data_org
        }
    }

    abnormal_level, ber_result = pd_monitor.task_processing(task=task_pack)["blade_detect"]
    plt.plot(ber_result)
    plt.show()


if __name__ == "__main__":
    task_test()
