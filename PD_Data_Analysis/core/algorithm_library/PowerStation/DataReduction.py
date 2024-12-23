#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====

import numpy as np
from scipy.signal import butter, filtfilt, hilbert


class DataRe:
    def __init__(self, sr: int):
        self.sr = sr

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

    def butterworth_filter(self, data: np.ndarray, bp_low: float, bp_high: float, bp_order: int):
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

    @staticmethod
    def rotational_freq(rotat, rotat_pulse: int, rotat_unit: str):
        """
        Convert rotational speed to frequency.
        :param rotat: float or 1D np.ndarray raw rotation data.
        :param rotat_pulse: number of pulsed of each rotation.
        :param rotat_unit: unit of "rotat", rpm or Hz
        :return: real rotational frequency in Hz
        """
        rotat_real = rotat / rotat_pulse

        if rotat_unit == 'rpm':
            rotat_Hz = rotat_real / 60
        elif rotat_unit == 'Hz':
            rotat_Hz = rotat_real
        else:
            print("未识别的转速单位。转速单位应为“rpm”或“Hz”。")

        return rotat_Hz

    def avg_rotat_freq(self, rotat_freq):
        """
        Calculate average rotational frequency.
        :param rotat_freq: float or 1D np.ndarray rotational frequency data.
        :param rotat_pulse: number of pulsed of each rotation.
        :param rotat_unit: unit of "rotat", rpm or Hz
        :return: averaged real rotational frequency in Hz
        """
        # rotat_Hz = self.rotational_freq(rotat, rotat_pulse, rotat_unit)
        rotat_avg = np.average(rotat_freq)

        return rotat_avg



