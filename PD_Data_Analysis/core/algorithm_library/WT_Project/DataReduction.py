#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====

import numpy as np
from scipy.signal import butter, filtfilt, iircomb, hilbert
import pandas as pd


class DataRe:
    def __init__(self, sr: int):
        self.sr = sr

    @staticmethod
    def to_julian(datetime: str):
        year = int(datetime[0:4])
        mon = int(datetime[4:6])
        day = int(datetime[6:8])
        hour = int(datetime[8:10])
        minute = int(datetime[10:12])
        sec = int(datetime[12:])

        ts = pd.Timestamp(year, mon, day, hour, minute, sec)
        jd = ts.to_julian_date() - 2400000.5
        return jd

    @staticmethod
    def hilbert_envelope(data: np.ndarray):
        """
        Hilbert transform to get envelope.
        :param data: 1D array to be transformed.
        :return: envelope
        """

        analytic_signal = hilbert(data)
        amp_env = np.abs(analytic_signal)
        return amp_env

    def butterworth_filter(self, data: np.ndarray, bp_low: int, bp_high: int, bp_order: int):
        """
        Use the Butterworth bandpass filter to split the data into the given frequency bands.
        :param bp_order: 滤波阶次
        :param bp_high: 带通频率上限
        :param bp_low: 带通频率下限
        :param data: 1D array; data to be filtered
        :return: 1D array; filtered data
        """
        [b, a] = butter(bp_order, [bp_low, bp_high], 'bandpass', fs=self.sr)
        filtered = filtfilt(b, a, data)
        return filtered

    def iircomb_filter(self, data: np.ndarray, w0: float, Q: float):
        """
        iircomb filter to filter harmonics.
        :param data: data to be filtered.
        :param w0: fundamental frequency of the comb filter. Must EVENLY divide the sampling rate.
        :param Q: Quality factor. Dimensionless parameter that characterizes notch filter -3 dB bandwidth bw relative to its center frequency, Q = w0/bw.
        :return: np.ndarray. Filtered data
        """
        [b, a] = iircomb(w0, Q, fs=self.sr)
        filtered = filtfilt(b, a, data)
        return filtered

    @staticmethod
    def apply_window(data: np.ndarray, window: str):
        """
        Return windowed data
        :param window: window type
        :param data: 1D; waveform
        :return: 1D; windowed waveform.
        """
        l = len(data)
        if window == 'bartlett':
            dw = data * np.bartlett(l)
        elif window == 'blackman':
            dw = data * np.blackman(l)
        elif window == 'hamming':
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
        """
        FFT to get the data spectrum.
        :param data: waveform
        :param window: windo type
        :return: 1D; spectrum
        """
        l = len(data)
        if window == 'bartlett':
            lw = np.sum(np.bartlett(l))
        elif window == 'blackman':
            lw = np.sum(np.blackman(l))
        elif window == 'hamming':
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

    def down_sampling(self, raw: np.ndarray, n: int) -> (np.ndarray, int):
        """
        Down sampling data.
        :param raw: 1D; data to be down-sampled.
        :param n: down-sampling orders.
        :return: 1D; down-sampled data.
        """

        if self.sr % n:
            raise ValueError("Down sampling order n should be able to divide the raw sampling rate evenly.")
        else:
            ds_sr = self.sr // n
            max_freq = ds_sr // 2

            [b, a] = butter(4, max_freq, 'low', fs=self.sr)
            filtered = filtfilt(b, a, raw)

            if len(filtered) % n:
                filtered = filtered[0: -(len(raw) % n)]
            filtered = filtered.reshape([-1, n])
            ds = filtered[:, 0].flatten()
            return ds, n
