#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
import numpy as np
from scipy.signal import butter, filtfilt


class DataPreparation:
    def __init__(self, configs):
        for key, val in configs.items():
            setattr(self, key, val)

    @staticmethod
    def remove_zero_drift(data: np.ndarray):
        avg = np.average(data)
        return data - avg

    def butterworth_filter(self, data: np.ndarray):
        [b, a] = butter(self.BP_filter["order"], [self.BP_filter["low"], self.BP_filter["high"]], 'bandpass', fs=self.sr)
        filtered = filtfilt(b, a, data)
        return filtered

    @staticmethod
    def apply_window(data: np.ndarray, window: str):
        l = len(data)
        if window == 'hamming':
            dw = data * np.hamming(l)
        elif window == 'hanning':
            dw = data * np.hanning(l)
        elif window == 'boxcar':
            dw = data
        else:
            raise ValueError(
                "Window type not recognized. Supported window types are boxcar(no window) bartlett, blackman, hamming, and hanning.")

        return dw

    def get_spectrum(self, data: np.ndarray, window: str = 'boxcar'):
        l = len(data)

        if window == 'hamming':
            lw = np.sum(np.hamming(l))
        elif window == 'hanning':
            lw = np.sum(np.hanning(l))
        elif window == 'boxcar':
            lw = l
        else:
            raise ValueError(
                "Window type not recognized. Supported window types are boxcar(no window) bartlett, blackman, hamming, and hanning.")

        dw = self.apply_window(data, window)
        ft = np.fft.rfft(dw)
        db = np.sqrt(2) * np.abs(ft) / lw
        db[0] = 0
        return db

    def data_reduction(self, raw):

        data = self.remove_zero_drift(raw)
        data = self.butterworth_filter(data)

        return data

    def data_reshape(self, data, clip_time):
        clip_len = int(clip_time * self.sr)
        tail = len(data) % clip_len
        if tail:
            data = data[:-tail]

        data_clips = data.reshape(-1, clip_len)

        return data_clips

    @staticmethod
    def rms(data):
        """
        Root-mean-square value of the blocks
        :param data: 1D or 2D array
        :return: 1D array; rms value
        """
        if len(data.shape) == 1:
            rms = np.sqrt(np.average(data ** 2))
            rms = np.array([rms])
        else:
            rms = np.sqrt(np.average(data ** 2, axis=1))

        return rms

    @staticmethod
    def pp_ratio(clips: np.ndarray):
        """
        pp-value ratio
        :param clips: 2d array, one data clip each row
        :return: 1d array, pp-value ratio
        """
        pps = np.max(clips, axis=1) - np.min(clips, axis=1)
        pp_ratio = pps[1:] / pps[:-1]

        return pp_ratio
