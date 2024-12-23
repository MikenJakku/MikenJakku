#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
import numpy as np
from scipy.signal import find_peaks


class Harmonics:
    def __init__(self, sr, delta_freq, minN_rms, window_ENBW, harmonic_orders, snr_th_1st):
        self.sr = sr
        self.delta_freq = delta_freq
        self.minN_rms = minN_rms
        self.window_ENBW = window_ENBW
        self.harmonic_orders = harmonic_orders
        self.snr_th_1st = snr_th_1st  # ratio of the 1st harmonic snr threshold relative to the higher levels.

    @staticmethod
    def __find_spectral_line(theoretical_freq: float, rotat_freq: float, spec_clip: np.ndarray,
                             freq_array: np.ndarray, rms_clip: float, spec_snr_th):
        """
        To find if there is the target spectral line in the given spectrum.
        :param freq_array: frequency array corresponding to the spec_clip.
        :param spec_clip: spectrum clip to look for the target spectral line.
        :param theoretical_freq: theoretical frequency of the harmonic when the rotational frequency is ValidatingData Hz.
        :param rotat_freq: rotational frequency in Hz.
        :param rms_clip: rms to calculate spectrum snr for the clip.
        :param spec_snr_th: spectrum SNR threshold
        :return: spectral line index, frequency, amplitude, and snr (all values are set to zero if there is no such line).
        """
        # find all the peaks in the spectral clip
        peak_idxs, _ = find_peaks(spec_clip)
        peak_amps = spec_clip[peak_idxs]

        if len(peak_idxs):
            which_peaks = np.argwhere(peak_amps >= (rms_clip * spec_snr_th)).flatten()
            peak_candi_id = peak_idxs[which_peaks]
            peak_candi_freq = freq_array[peak_candi_id]
        else:
            peak_candi_freq = []
            peak_candi_id = []

        if len(peak_candi_freq):
            which_candi = np.argmin(np.abs(peak_candi_freq - theoretical_freq * rotat_freq))
            peak_freq = peak_candi_freq[which_candi]
            peak_id = peak_candi_id[which_candi]
            peak_amp = spec_clip[peak_id]
            peak_snr = peak_amp / rms_clip
        else:
            peak_freq = 0
            peak_id = 0
            peak_amp = 0
            peak_snr = 0

        return peak_id, peak_freq, peak_amp, peak_snr

    def __spec_clip(self, full_spec: np.ndarray, theoretical_freq: float, rotat_freq: float):
        """
        Get the spectrum clips for spectral-line searching and rms calculation.
        :param rotat_freq: rotational frequency.
        :param full_spec: np.ndarray. Spectrum of [0 Hz, sr//2 Hz]
        :param theoretical_freq: theoretical frequency of the harmonic when the rotational frequency is ValidatingData Hz.
        :return: rms: float, local rms to calculate SNR.
                 spectrum_clip: spectrum clip to search for the targe line.
                 freq_array_clip: frequency array clip to search for the targe line.
                 idx_low: start index of the spectrum clip in the full spectrum.
        """
        freq_array = np.linspace(0, self.sr // 2, len(full_spec))

        # Get spectrum clip for target-line searching.
        delta_freq = self.delta_freq

        # (ValidatingData) To consider the uncertainty in rotational frequency:
        # tar_freq_low = theoretical_freq * (rotat_freq - delta_freq)
        # tar_freq_high = theoretical_freq * (rotat_freq + delta_freq)

        # or (2) To assume accurate rotational frequency and uncertainty in frequency resolution
        tar_freq_low = theoretical_freq * rotat_freq - delta_freq
        tar_freq_high = theoretical_freq * rotat_freq + delta_freq

        if tar_freq_low < 0:
            tar_freq_low = 0

        idx_low = np.argwhere(freq_array < tar_freq_low).flatten()[-1]
        idx_high = np.argwhere(freq_array > tar_freq_high).flatten()[0]

        spectrum_clip = full_spec[idx_low: idx_high + 1]
        freq_array_clip = freq_array[idx_low: idx_high + 1]

        if len(spectrum_clip) < self.minN_rms:
            N_padding = int(np.ceil((self.minN_rms - len(spectrum_clip)) / 2))
            rms_idx_low = idx_low - N_padding
            rms_idx_high = idx_high + N_padding
            if rms_idx_low < 0:
                rms_idx_low = 0
            spec_clip_for_rms = full_spec[rms_idx_low: rms_idx_high + 1]
        else:
            spec_clip_for_rms = spectrum_clip

        # remove the maximum value to calculate the rms of the clip, in case that the clip is too short
        # thus the peak may severely affect the rms value
        max3_spec_id = np.argsort(spec_clip_for_rms)[-3:]
        clip_without_max = np.delete(spec_clip_for_rms, max3_spec_id)
        rms_clip = np.sqrt(np.average(clip_without_max ** 2))

        return spectrum_clip, freq_array_clip, idx_low, rms_clip

    def find_harmonics(self, full_spec: np.ndarray, base_freq: float, rotat_freq: float, spec_snr_th):
        """
        Extract harmonics from the spectrum, if there is any.
        :param full_spec: np.ndarray. Spectrum of [0 Hz, sr//2 Hz]
        :param base_freq: base frequency of defect at ValidatingData Hz
        :param rotat_freq: rotational frequency
        :param spec_snr_th: spectrum SNR threshold
        :return:
        """
        harmonic_matrix = np.zeros([self.harmonic_orders, 5])
        freq_array = np.linspace(0, self.sr // 2, len(full_spec))

        for n in range(self.harmonic_orders):
            order = n + 1
            if order == 1:
                spec_snr_th = spec_snr_th * self.snr_th_1st

            # theoretical frequency of the harmonic when the rotational frequency is ValidatingData Hz.
            theoretical_freq = base_freq * order
            spectrum_clip, freq_array_clip, idx_low, rms_clip = self.__spec_clip(full_spec, theoretical_freq,
                                                                                 rotat_freq)
            peak_idx, peak_freq, peak_amp, peak_snr = \
                self.__find_spectral_line(theoretical_freq, rotat_freq, spectrum_clip, freq_array_clip, rms_clip,
                                          spec_snr_th)
            peak_idx = peak_idx + idx_low
            if peak_idx and peak_freq and peak_amp:
                harmonic_matrix[n] = order, peak_idx, freq_array[peak_idx], full_spec[peak_idx], peak_snr

        no_detection_id = np.argwhere(harmonic_matrix[:, 0] == 0).flatten()
        harmonic_matrix = np.delete(harmonic_matrix, no_detection_id, axis=0)
        if len(harmonic_matrix) and (harmonic_matrix[0, 0] > 1):
            harmonic_matrix = np.array([])

        return harmonic_matrix
