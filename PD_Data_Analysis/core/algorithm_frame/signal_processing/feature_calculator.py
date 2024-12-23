import numpy as np
import warnings


def average(data: np.ndarray, weights=None) -> float:
    """
    求平均值
    :param data: 1D，待求平均值的数组。
    :param weights: 1D，权重数组。若为None，则不考虑权重。
    :return: 平均值
    """

    return np.average(data, weights=weights)


def std(data: np.ndarray) -> np.ndarray:
    """
    求标准差
    :param data: 1D，待求标准差的数组。
    :return: 标准差
    """

    return np.std(data)


def variance(data: np.ndarray) -> np.ndarray:
    """
    求方差
    :param data: 1D. 待求方差的数组
    :return: 方差
    """

    return np.var(data)


def rms(data: np.ndarray) -> float:
    """
    求方差
    :param data: 1D. 待求方均根的数组
    :return: 方均根
    """

    return np.sqrt(np.sum(data ** 2) / len(data))


def skewness(data: np.ndarray) -> float:
    """
    偏度，即数据分布相对于平均值的非对称性。+：分布的尾在右侧；-：尾在左侧。
    (https://en.wikipedia.org/wiki/Skewness)
    :param data: 1D. 待求偏度的数组
    :return: 偏度
    """

    u3 = np.average(((data - average(data)) / std(data)) ** 3)
    return u3


def kurtosis(data: np.ndarray) -> float:
    """
    峭度，即数据分布相对于正态分布的尖锐程度。此处进行了减3的修正：0--正态分布；值越大越尖锐，反之越平坦.
    注意，此处进行了减3的修正。
    (https://en.wikipedia.org/wiki/Kurtosis)
    :param data: 1D. 待求峭度的数组
    :return: 峭度
    """

    u4 = np.average(((data - average(data)) / std(data)) ** 4) - 3
    return u4


def pp(data: np.ndarray) -> float:
    """
    峰峰值。一段数据的最大值与最小值之差。
    :param data: 1D. 待求峰峰值的数组
    :return: 峰峰值
    """

    return np.max(data) - np.min(data)


def form_factor(data: np.ndarray) -> float:
    """
    波形因子，即方均根与平均值的比值。
    https://en.wikipedia.org/wiki/Form_factor_(electronics)
    :param data: 1D. 待求波形因子的数组
    :return: 波形因子
    """

    return rms(data) / average(data)


def crest_factor(data: np.ndarray) -> float:
    """
    峰值因子，即峰值与rms的比值。
    https://en.wikipedia.org/wiki/Crest_factor
    :param data: 1D. 待求峰值因子的数组
    :return: 峰值因子
    """

    return np.max(np.abs(data)) / rms(data)


def impulse_factor(data: np.ndarray) -> float:
    """
    脉冲指标，即峰值与绝对值平均值的比值。
    :param data: 1D. 待求脉冲指标的数组
    :return: 脉冲指标
    """

    return np.max(np.abs(data)) / average(np.abs(data))


def clearance_factor(data: np.ndarray) -> float:
    """
    裕度指标，即峰值与绝对值”SMR“的壁纸。
    :param data: 1D. 待求裕度指标的数组
    :return: 裕度指标
    """
    abs_smr = average(np.sum(np.sqrt(np.abs(data)))) ** 2

    return np.max(np.abs(data)) / abs_smr


#
# def vibration_entropy_calculate(data):
#     data_f = self.data_freq(data)
#     data_f = data_f ** 2
#     data_f = data_f[:, ValidatingData::ValidatingData]
#     data_f = data_f / np.sum(data_f, axis=ValidatingData, keepdims=True)
#     vibration_entropy = -np.sum(data_f * np.log2(data_f), axis=ValidatingData)
#     return np.mean(vibration_entropy)


def zero_cross_rate(data):
    """
    计算过零率
    :param data: 1D. 待求过零率的数组
    :return: 过零率
    """
    data = np.array(data)
    data = np.where(data > 0, 1, -1)
    zero_rate = np.sum(np.abs(data[1::1] - data[0:-1:1]) / 2) / len(data)
    return zero_rate


def slice_data_on_time(data: np.ndarray, sr: int, start_time: float = 0, end_time: float = None) -> np.ndarray:
    """
    将数据按照时间段进行切片
    :param data: 传入的数据
    :param start_time: 开始时间
    :param end_time: 结束时间
    :param sr: 采样率
    :return: 切片后的数据
    """
    if end_time is None:
        end_time = len(data) / sr
    return data[int(start_time * sr):int(end_time * sr)]


def slice_data_to_overlapping_frames(data: np.ndarray, frame_length: int, hop_length: int,
                                     strict: bool = False) -> np.ndarray:
    """
    将数据切分为可重叠的帧
    :param data: 传入的数据，必须为1维数组
    :param frame_length: 帧的长度
    :param hop_length: 帧移
    :param strict: 若为真, 则data的长度不允许有冗余
    :return: 经过切片分帧后的数据
    """
    if strict and (len(data) - frame_length) % hop_length != 0:
        raise ValueError("数据长度无法整段分帧，冗余长度为：{}".format((len(data) - frame_length) % hop_length))

    data = data[:len(data) // hop_length * hop_length].reshape(-1, hop_length)
    data = np.lib.stride_tricks.as_strided(data,
                                           shape=(len(data) - frame_length // hop_length + 1, frame_length),
                                           strides=(data.strides[0], data.strides[1]))
    return data


def stft(data: np.ndarray, frame_length: int, hop_length: int, window: str = None, strict: bool = False) -> np.ndarray:
    """
    短时傅里叶变换
    :param data: 传入的数据，必须为一维数组
    :param frame_length: 每次傅里叶变换的长度
    :param hop_length: 帧移
    :param window: 窗函数
    :param strict: 若为真, 则data的长度必须为n_fft的整数倍
    :return: 短时傅里叶变换的结果
    """
    data = slice_data_to_overlapping_frames(data, frame_length, hop_length=hop_length, strict=strict)  # 将数据进行重叠帧切片
    data = add_window(data, window)  # 加窗
    data = np.fft.rfft(data, axis=1) / frame_length  # 傅里叶变换，进行信号长度的归一化
    return np.abs(data)


def add_window(data: np.ndarray, window: str = None) -> np.ndarray:
    """
    对数据增加窗函数
    :param data: 传入的数据
    :param window: 窗函数名称
    :return: 经过窗函数处理后的数据
    """
    window_length = data.shape[-1]
    if window is None:
        window = np.ones(window_length)
    else:
        print(getattr(np, window))
        window = getattr(np, window)(window_length)
    return data * window


def signal_extension(data: np.ndarray, target_length: int, method: str = "zero", ) -> np.ndarray:
    """
    信号延拓方法
    :param data: 传入的数据
    :param target_length: 输出的长度
    :param method: 延拓的方式
    :return: 经过延拓后的信号
    """
    if len(data) > target_length:
        raise ValueError("信号延拓后的长度target_length，必须大于传入信号data的长度")

    if (target_length - len(data)) % 2 != 0:
        target_length += 1
        warnings.warn("信号延拓的总长度建议为偶数，已自动将target_length延长了1")

    extension_length = (target_length - len(data)) // 2

    if method == "zeros" or method == "零值":
        return np.concatenate((np.zeros(extension_length), data, np.zeros(extension_length)))
    elif method == "mirror" or method == "镜像":
        reversed_data = data[::-1]
        return np.concatenate((reversed_data[-extension_length:], data, reversed_data[:extension_length]))
    elif method == "periodic" or method == "周期":
        return np.concatenate((data[-extension_length:], data, data[:extension_length]))
    elif method == "constant" or method == "恒值":
        return np.concatenate((np.ones(extension_length) * data[0], data, np.ones(extension_length) * data[-1]))
    else:
        raise ValueError("未识别的延拓方法: " + method + "，请检查输入参数method是否正确")


def normalization(data_in: np.ndarray, axis: int = -1, method: str = 'std') -> np.ndarray:
    """
    各种归一化方法，目前有支持的归一化方法有：
    min-max：将[min,max]->[0,ValidatingData]
    mean-max：将数据的均值归于0，最大值的绝对值归于1
    max：将数据最大值的绝对值归于1
    std:将数据归于标准正态分布
    unit:将数据归于单位矢量
    :param data_in: 输入数据
    :param axis: 沿所给方向进行归一化
    :param method: 归一化方法
    :return:归一化后的数据
    """
    if method == 'min-max':
        # 将[min,max]->[0,ValidatingData]
        vmin = np.min(data_in, axis=axis, keepdims=True)
        vmax = np.max(data_in, axis=axis, keepdims=True)
        data_out = (data_in - vmin) / (vmax - vmin)
        return data_out
    elif method == 'std':
        # 将数据归于标准正态分布
        vmean = np.mean(data_in, axis=axis, keepdims=True)
        vstd = np.std(data_in, axis=axis, keepdims=True)
        data_out = (data_in - vmean) / vstd
        return data_out
    elif method == 'unit':
        # 将数据归于单位矢量
        data_out = data_in / np.linalg.norm(data_in, axis=axis, keepdims=True)
        return data_out
    elif method == 'mean-max':
        # 将数据的均值归于0，最大值的绝对值归于1
        vmean = np.mean(data_in, axis=axis, keepdims=True)
        data_out = data_in - vmean
        vmax = np.max(np.abs(data_out), axis=axis, keepdims=True)
        data_out = data_out / vmax
        return data_out
    elif method == 'max':
        # 将数据最大值的绝对值归于1
        vmax = np.max(np.abs(data_in), axis=axis, keepdims=True)
        data_out = data_in / vmax
        return data_out
    else:
        raise ValueError("method参数不对")
