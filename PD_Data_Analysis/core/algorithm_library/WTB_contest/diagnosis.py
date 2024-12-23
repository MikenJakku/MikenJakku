#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
from core.algorithm_library.WTB_contest.reduction_statistics import DataPreparation
import numpy as np
from scipy.signal import stft


class Diagnosis:
    def __init__(self, configs):
        for key, val in configs.items():
            setattr(self, key, val)

    def defect_detection(self, data):
        configs = self.__dict__
        dp_tools = DataPreparation(configs)

        ibers = self.iber_calculator(data)

        clips_pp = dp_tools.data_reshape(data, self.pp_time)
        pp_ratio = dp_tools.pp_ratio(clips_pp)

        clips_rms = dp_tools.data_reshape(data, self.rms_time)
        rmss = dp_tools.rms(clips_rms)

        if any(np.array(rmss) < self.stop_rms_th):
            status = "0"
        elif any(np.array(pp_ratio) > self.pia_pp_ratio_th):
            status = "2"
        elif any(np.array(ibers) > self.rustle_iBER_th):
            status = '2'
        else:
            status = 'ValidatingData'

        return {"status": status, "iBER": np.max(np.array(ibers)),
                "pp_ratio": np.max(np.array(pp_ratio)), "rms": np.average(np.array(rmss))}

    def iBER_self_define(self, data, split_idx):
        """
        自定义iBER计算
        """
        data = data ** 2
        iBER = np.sum(data[split_idx:]) / np.sum(data[:split_idx])
        return iBER

    def iber_calculator(self, data, check=False):
        slice_len = int(self.pp_time * self.sr)
        data = data[:len(data) // slice_len * slice_len]  # 取整切片数据

        iber_result = []

        freq_axis, time_axis, spectrum = stft(data, fs=self.sr,
                                              nperseg=slice_len,
                                              noverlap=0,
                                              nfft=slice_len)

        freq_start_idx = np.argmin(np.abs(freq_axis - self.BP_filter["low"]))
        freq_end_idx = np.argmin(np.abs(freq_axis - self.BP_filter["high"]))
        spectrum = np.abs(spectrum[freq_start_idx:freq_end_idx, :])
        split_idx = np.argmin(np.abs(freq_axis - self.split_freq))

        for j in range(spectrum.shape[1]):
            spectrum_data = spectrum[:, j]  # 取一个切片的时频数据

            _data_iBER = self.iBER_self_define(spectrum_data, split_idx)
            iber_result.append(_data_iBER)

        if check:
            print("data_check: data_shape=", data.shape)
            print("window function: ", "hann")
            print("data_check: stft shape=", spectrum.shape)
            print("data_check: freq_start_idx=", freq_start_idx)
            print("data_check: freq_end_idx=", freq_end_idx)
            print("data_check: split_idx=", split_idx)
            print("data_check: iber_result shape=", len(iber_result))
            print("data_check: iber_first_result=", iber_result[0])
            print("data_check: iber_last_result=", iber_result[-1])

        return iber_result
