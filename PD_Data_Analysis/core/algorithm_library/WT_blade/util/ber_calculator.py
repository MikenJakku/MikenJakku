#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
import numpy as np
from scipy.signal import stft

# 预设的参数们
sr = 48000
slice_len = int(0.2 * sr)
high_freq = 20000
low_freq = 2000
split_freq = 5000


def BER_self_define(data, split_idx):
    """
    自定义BER计算
    """
    data = data ** 2
    BER = np.sum(data[split_idx:]) / np.sum(data[:split_idx])
    return BER


def ber_calculate(data, check=False):
    data = data[:len(data) // slice_len * slice_len]  # 取整切片数据

    ber_result = []

    freq_axis, time_axis, spectrum = stft(data, fs=sr,
                                          nperseg=slice_len,
                                          noverlap=0,
                                          nfft=slice_len)

    freq_start_idx = np.argmin(np.abs(freq_axis - low_freq))
    freq_end_idx = np.argmin(np.abs(freq_axis - high_freq))
    spectrum = np.abs(spectrum[freq_start_idx:freq_end_idx, :])
    split_idx = np.argmin(np.abs(freq_axis - split_freq))

    for j in range(spectrum.shape[1]):
        spectrum_data = spectrum[:, j]  # 取一个切片的时频数据

        _data_BER = BER_self_define(spectrum_data, split_idx)
        ber_result.append(_data_BER)

    if check:
        print("data_check: data_shape=", data.shape)
        print("window function: ", "hann")
        print("data_check: stft shape=", spectrum.shape)
        print("data_check: freq_start_idx=", freq_start_idx)
        print("data_check: freq_end_idx=", freq_end_idx)
        print("data_check: split_idx=", split_idx)
        print("data_check: ber_result shape=", len(ber_result))
        print("data_check: ber_first_result=", ber_result[0])
        print("data_check: ber_last_result=", ber_result[-1])

    return ber_result


if __name__ == "__main__":
    data_random = np.random.random(sr * 60)
    ber = ber_calculate(data_random, check=True)
    print(ber)
