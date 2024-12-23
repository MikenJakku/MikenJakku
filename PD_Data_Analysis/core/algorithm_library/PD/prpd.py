"""
对外接口：get_prpd_data，传入一个一维信号，返回一个小波变换后的重建信号
"""

import numpy as np
import pywt


def get_prpd_data(signal: np.ndarray, config) -> tuple:
    """外部接口：计算prpd"""
    signal_A2 = __get_A2_from_D1(signal)  # 二级小波变换
    signal_aligned, max_index = __get_aligned_signal(signal_A2, config)  # 峰对齐

    if np.max(signal_aligned) <= 0:
        signal_prpd_norm = np.zeros_like(signal_aligned)
    else:
        signal_prpd_norm = signal_aligned / np.max(signal_aligned)  # 归一化

    return signal_prpd_norm, max_index  # fixme: 在这里返回了一个最大索引的信息


def __get_aligned_signal(signal: np.ndarray, config) -> tuple:
    """峰对齐，将峰值对齐到90度和270度上"""
    result = np.zeros_like(signal)
    max_index = np.argmax(np.abs(signal))  # 查找signal中最大值的索引，又重复取了一遍abs

    if max_index < config.first_peak_idx:
        tail_len = config.first_peak_idx - max_index
        result[0:tail_len] = signal[-tail_len:]
        result[tail_len:] = signal[0:config.signal_length - tail_len]
    else:
        max_index = max_index - config.first_peak_idx
        result[:(config.signal_length - max_index)] = signal[max_index:]
        result[(config.signal_length - max_index):] = signal[:max_index]
    return result, max_index  # fixme: 在这里返回了一个最大索引的信息


def __WT(signal: np.ndarray, wavelet=None, level=1, mode=None):
    """
    小波变换
    返回的系数：[cA_n, cD_n, cD_n-ValidatingData, …, cD2, cD1]
    """
    assert wavelet and mode is not None, "参数不能为空"

    coeffs = pywt.wavedec(signal, wavelet=wavelet, mode=mode, level=level, axis=-1)
    return coeffs


def __IWT(coeffs, wavelet=None, mode=None):
    """
    小波逆变换
    传入参数，第一项为A，其余为D
    """
    assert wavelet and mode is not None, "参数不能为空"

    x = pywt.waverec(coeffs, wavelet=wavelet, mode=mode)
    return x


def __eliminate_signal_approximations(signal: np.ndarray, wavelet=None, mode=None) -> np.ndarray:
    """去除近似项，获取信号的细节信息"""
    coeffs = __WT(signal, wavelet=wavelet, mode=mode)
    coeffs[0] = np.zeros_like(coeffs[0])
    signal_details = __IWT(coeffs, wavelet=wavelet, mode=mode)
    return signal_details


def __eliminate_signal_details(signal: np.ndarray, wavelet=None, mode=None) -> np.ndarray:
    """去除细节项，获取信号的近似信息"""
    coeffs = __WT(signal, wavelet=wavelet, mode=mode)
    coeffs[-1] = np.zeros_like(coeffs[-1])
    signal_approximations = __IWT(coeffs, wavelet=wavelet, mode=mode)
    return signal_approximations


def __get_A2_from_D1(signal: np.ndarray) -> np.ndarray:
    """获取小波去噪后的结果"""
    signal_D1 = __eliminate_signal_approximations(signal, wavelet='db1', mode='symmetric')
    signal_A2 = __eliminate_signal_details(signal_D1, wavelet="coif1", mode='symmetric')
    signal_A2_abs = np.abs(signal_A2)

    return signal_A2_abs
