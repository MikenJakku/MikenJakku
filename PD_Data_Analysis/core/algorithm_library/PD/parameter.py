def get_parameter(sr=96000):
    """
    动态调整配置文件，返回配置实例
    """
    para = ReadConfig()
    para.sr = sr  # 采样率
    para.power_frequency = 50  # 工频周期
    para.signal_length = int(sr / para.power_frequency)  # 信号长度
    para.first_peak_idx = int(sr / para.power_frequency / 4) - 1  # 首峰索引

    para.narrow_width = 200 * sr / 96000  # 窄峰宽
    para.surface_width = 300 * sr / 96000  # 沿面峰宽
    para.wide_width = para.signal_length / 4  # 宽峰宽
    para.peak_left = int(para.signal_length / 8)
    para.peak_right = int(para.signal_length / 2 - para.peak_left)

    para.phase_diff_threshold = para.signal_length / 8  # 相位对其阈值

    return para


class ReadConfig(object):
    # 局放代号定义
    no_discharge = int(0)  # 不放电
    corona_discharge = int(1)  # 电晕放电
    double_discharge = int(2)  # 双峰放电
    suspended_discharge = int(3)  # 悬浮放电
    surface_discharge = int(4)  # 沿面放电

    lowest_noise_amp = 0.2  # 最小噪音
    highest_noise_amp = 0.5  # 最大噪音

    sr = 96000  # 采样率
    power_frequency = 50  # 工频周期
    signal_length = int(sr / power_frequency)  # 信号长度
    first_peak_idx = int(sr / power_frequency / 4) - 1  # 首峰索引

    narrow_width = 200 * sr / 96000  # 窄峰宽
    surface_width = 300 * sr / 96000  # 沿面峰宽
    wide_width = signal_length / 4  # 宽峰宽
    peak_left = int(signal_length / 8)
    peak_right = int(signal_length / 2 - peak_left)

    phase_diff_threshold = signal_length/8  # 相位对其阈值

    PD_num_rate = 0.85  # 峰集中程度界限

    alarm_length = 100  # 报警队列的长度
    PD_num = 5  # 连续放电次数阈值

    PD_rate_threshold = 0.85  # 局放占比阈值
    PD_rate_num_threshold = PD_rate_threshold * alarm_length  # 在队列中的数量

    double_prefer = 20  # 对双峰放电的偏好阈值

    using_channel = 14  # 使用的通道数
    debug = False  # debug开关
