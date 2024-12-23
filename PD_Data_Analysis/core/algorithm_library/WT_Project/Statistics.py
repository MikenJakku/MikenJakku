#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
from core.algorithm_library.WT_Project.DataReduction import DataRe
import numpy as np


class Stat:
    def __init__(self, sr: int, window_ENBW, GBT):
        self.sr = sr
        self.enbw_pars = window_ENBW
        self.GBT_pars = GBT

    # ---------- Statistical values ---------- #
    def oa_and_statistics(self, raw: np.ndarray, pos: str, window='boxcar'):
        """
        Overall acceleration. Full frequency when freq_low and freq_high are both None.
        :param window: window type of the FFT window.
        :param raw: 1D array; waveform
        :param pos: str; position of the
        """
        dr = DataRe(self.sr)

        data = dr.apply_window(raw, window)
        enbw = self.enbw_pars[window][0]

        spectrum = dr.get_spectrum(data, window=window)

        if pos.startswith('shaft'):
            key = 'shaft'
        elif pos.startswith('stator'):
            key = 'stator'
        elif pos.startswith('gearbox_input'):
            key = 'gearbox_low'
        elif pos.startswith('generator'):
            key = 'generator'
        else:
            key = 'gearbox_high'

        bp_key = "GBT_" + key + '_bp'
        bp = self.GBT_pars[bp_key]
        freq_low, freq_high = bp

        freq = np.linspace(0, self.sr // 2, len(spectrum))

        low_idx = np.argwhere(freq >= freq_low).flatten()[0]
        high_idx = np.argwhere(freq <= freq_high).flatten()[-1]
        spec = spectrum[low_idx: high_idx]

        wave = dr.butterworth_filter(raw, freq_low, freq_high, 2)

        oa = np.sqrt(np.sum(spec ** 2) / enbw)
        pp = self.pp(wave)[0]
        avg = self.avg(np.abs(wave))[0]
        std = self.std(wave)[0]
        skew = self.skewness(wave)[0]
        kurt = self.kurtosis(wave)[0]
        crest = self.crest(wave)[0]

        return oa, pp, avg, std, skew, kurt, crest

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
    def pp(data: np.ndarray):
        """
        Peak-to-peak value
        :param data: 1D or2D array; input blocks
        :return: 1D array; peat-to-peak value
        """
        if len(data.shape) == 1:
            pp = np.array([np.max(data) - np.min(data)])
        elif len(data.shape) == 2:
            pp = np.max(data, axis=1) - np.min(data, axis=1)
        else:
            raise ValueError("Input data should be 1D or 2D.")

        return pp

    @staticmethod
    def avg(data):
        """
        Average value of the blocks
        :param data: 1D/2D array, input blocks
        :return: 1D array, average.
        """
        if len(data.shape) == 1:
            avg = np.array([np.average(data)])
        elif len(data.shape) == 2:
            avg = np.average(data, axis=1)
        else:
            raise ValueError("Input data should be 1D or 2D.")

        return avg

    @staticmethod
    def std(data):
        """
        Standard deviation of the blocks
        :param data: 1D or 2d array
        :return: 1D array
        """
        if len(data.shape) == 1:
            std_dev = np.array([np.std(data)])
        elif len(data.shape) == 2:
            std_dev = np.std(data, axis=1)
        else:
            raise ValueError("Input data should be 1D or 2D.")

        return std_dev

    def skewness(self, data):
        """
        Skewness of the blocks, i.e., the asymmetry of the probability distribution about its mean.
        Positive: tail on the right; negative: tail on the left; zero: tails on both sides of the mean balance out overall
        (https://en.wikipedia.org/wiki/Skewness)
        :param data:
        :return:
        """
        avgs = self.avg(data)
        avgs = np.transpose([avgs])

        if len(data.shape) == 1:
            a = np.sum((data - avgs) ** 3) / data.shape[0]
        elif len(data.shape) == 2:
            a = np.sum((data - avgs) ** 3, axis=1) / data.shape[1]
        else:
            raise ValueError("Input data should be 1D or 2D.")

        b = self.std(data) ** 3

        return a / b

    def kurtosis(self, data):
        """
        Kurtosis of the blocks.
        Sharpness of a distribution compared with a normal distribution.
        0: normal distribution; the larger the shaper.
        (https://en.wikipedia.org/wiki/Kurtosis)
        :param data: 1D or 2D array
        :return: 1D array
        """
        avgs = self.avg(data)
        avgs = np.transpose([avgs])

        if len(data.shape) == 1:
            a = np.sum((data - avgs) ** 4) / data.shape[0]
        elif len(data.shape) == 2:
            a = np.sum((data - avgs) ** 4, axis=1) / data.shape[1]
        else:
            raise ValueError("Input data should be 1D or 2D.")

        b = self.std(data) ** 4

        return a / b - 3

    def crest(self, data: np.ndarray, rms: float = 0):
        """
        Crest indicator/factor
        :param rms: rms of the data. rms==0: use rms of the input data; rms != 0: use the input value,
                    e.g. to calculate the crest factor of a clip from the entire data array.
        :param data: input data.
        :return:
        """
        if len(data.shape) == 1:
            m = np.max(np.abs(data))
        elif len(data.shape) == 2:
            m = np.max(np.abs(data), axis=1)
        else:
            raise ValueError("Input data should be 1D or 2D.")

        if rms:
            r = rms
        else:
            r = self.rms(data)

        return m / r
