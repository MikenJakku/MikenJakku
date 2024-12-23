"""
变压器在线监测的配置文件transformer_config
        直流偏磁：对应：奇偶次谐波比
        重过载：对应：基频(100Hz)能量占比
        绕组变形：对应：振动熵
"""


class transformer_config:
    feature_list = ['odd_even_ratio', 'base_freq_ratio', 'vibration_entropy', 'rms_value', 'normal_vibra_ratio',
                    'main_freq_ratio', 'peak_peak_value']

    fault_type = {  # 异常类型，'fault_code':异常编码，'threshold':异常阈值，'desc':异常描述
        'odd_even_ratio': {'fault_code': 1, 'threshold': 0.3, 'desc': '直流偏磁'},
        'base_freq_ratio': {'fault_code': 2, 'threshold': 0.8, 'desc': '重过载'},
        'vibration_entropy': {'fault_code': 4, 'threshold': 3, 'desc': '绕组变形'},
        'normal_vibra_ratio': {'fault_code': 8, 'threshold': 0.5, 'desc': '干扰太强，检测无效'},
        # 'main_freq_ratio': {'fault_code': None, 'threshold': 0.3, 'desc': '铁心松动'},
    }

    trend_list = [
        'odd_even_ratio', 'base_freq_ratio', 'vibration_entropy', 'rms_value', 'normal_vibra_ratio',
        'main_freq_ratio', 'peak_peak_value']

    thresh_alarm = 0.3  # 异常数据占比的阈值，用于长时（天、月、年）报警，输入多段数据的特征，计算异常出现的频率，与此阈值比较


class feature_parameter:
    frame_time = 0.5  # 每帧的时间长度
    max_freq = 1200  # 本体振动的最大频率
    power_freq = 50  # 工频
    interval_freq = 4  # 计算频点值的取值范围
    fmin_freq = 40  # 计算低频段的能量范围【fmin:fmax】
    fmax_freq = 1200
