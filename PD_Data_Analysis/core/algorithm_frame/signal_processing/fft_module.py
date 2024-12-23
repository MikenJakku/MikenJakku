import numpy as np


def fft(data, window=None):
    """
    傅里叶变换
    :param data: 传入的数据
    :param window: 窗函数
    :return: 傅里叶变换后的数据
    """

    fft_data = np.fft.rfft(add_window(data, window=window))
    return fft_data


def select_spectrum(fft_data, sr, low_freq, high_freq):
    """
    选择特定频率范围
    :param fft_data: 傅里叶变换后的数据
    :param sr: 采样率
    :param low_freq: 低频
    :param high_freq: 高频
    :return: 特定频率范围内的数据
    """
    fft_index = np.fft.rfftfreq(len(fft_data)*2-1, 1 / sr)
    fft_data[(fft_index < low_freq) | (fft_index > high_freq)] = 0
    return fft_data


def bandpass_spectrum(data, sr, low_freq, high_freq, window=None):
    """
    带通滤波器
    :param data: 传入的数据
    :param sr: 采样率
    :param low_freq: 低频
    :param high_freq: 高频
    :param window: 窗函数
    :return: 滤波后的数据
    """
    fft_data = fft(data, window=window)

    return select_spectrum(fft_data, sr, low_freq, high_freq)


def bandpass_filter(data, sr, low_freq, high_freq, window=None):
    """
    带通滤波器
    :param data: 传入的数据
    :param sr: 采样率
    :param low_freq: 低频
    :param high_freq: 高频
    :param window: 窗函数
    :return: 滤波后的数据
    """
    fft_data = bandpass_spectrum(data, sr, low_freq, high_freq, window=window)
    return np.fft.irfft(fft_data)


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
