from core.algorithm_frame.base_class.monitor_base import MonitorBase
from core.algorithm_library.PD.Alarm import PDAlgorithm
import numpy as np
import soundfile as sf
from core.algorithm_frame.signal_processing.signal_processing import replace_nan_with_mean

class PDMonitor(MonitorBase):
    def init_algorithm(self):
        """
        初始化算法类
        抽象方法，在子类中必须进行实现。监测对象中应当至少含有一个算法类对象。
        """
        self.algorithm_dict["general"] = PDAlgorithm()



def task_test(data_org, sr):
    task_pack = {
        'task_type': ["PD"],
        'algorithm_name': "general",
        'data_pack': {
            "sample_rate": sr,
            'data': data_org
        }
    }
    pd_monitor = PDMonitor(config_name="PD.json", user="server")
    temp_result = pd_monitor.task_processing(task=task_pack)

    print(temp_result)

    # 处理prpd和significance异常值
    prpd = temp_result['PD']['prpd']
    significance = temp_result['PD']['significance']

    prpd = replace_nan_with_mean(prpd).tolist()
    significance = replace_nan_with_mean(significance).tolist()

    # 拷贝temp_result给handle_result
    handle_result = temp_result.copy()
    handle_result['PD']['prpd'] =  prpd
    handle_result['PD']['significance'] =  significance

    print('*** 处理nan以后： ***')
    print(handle_result)

    Time1 = handle_result['PD']['pd_start_time']
    Time2 = handle_result['PD']['pd_end_time']
    print("【讨论点1】Time1={} Time2={}".format(Time1, Time2))
    print((Time2-Time1) * 1000)



if __name__ == "__main__":
    # 读取数据 #
    data_path = r"F:\声纹\声纹数据\声纹统一平台测试数据\测试终端-105-TXSW00000059-20240223164643采取的文件.wav"
    data_org, sr = sf.read(data_path)
    print("原始采样率为", sr)

    task_test(data_org, sr)
