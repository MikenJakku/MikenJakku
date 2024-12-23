#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
from core.algorithm_library.PowerStation.DataReduction import DataRe
import numpy as np


class Stat:
    def __init__(self, sr: int, window_ENBW):
        self.sr = sr
        self.enbw_pars = window_ENBW

    # ---------- Statistical values ---------- #
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

    def oa(self, raw: np.ndarray, freq_low: float, freq_high: float, window='boxcar'):
        """
        Overall acceleration. Full frequency when freq_low and freq_high are both None.
        :param window: window type of the FFT window.
        :param raw: 1D array; waveform.
        :param freq_low: float.
        :param freq_high: float.
        """
        dr = DataRe(self.sr)

        data = dr.apply_window(raw, window)
        enbw = self.enbw_pars[window][0]

        spectrum = dr.get_spectrum(data, window=window)

        freq = np.linspace(0, self.sr // 2, len(spectrum))

        low_idx = np.argwhere(freq >= freq_low).flatten()[0]
        high_idx = np.argwhere(freq <= freq_high).flatten()[-1]
        spec = spectrum[low_idx: high_idx]

        oa = np.sqrt(np.sum(spec ** 2) / enbw)

        return oa
