import warnings
import numpy as np


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


def replace_nan_with_mean(arr: np.ndarray) -> np.ndarray:
    """
    将np数组中的nan值替换为均值
    """
    arr_ = np.array(arr)
    if np.isnan(arr_).any():
        mean_value = np.nanmean(arr_)
        arr_[np.isnan(arr_)] = mean_value

    return arr_