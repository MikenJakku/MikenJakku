#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
import numpy as np
from core.algorithm_library.WT_Project.Statistics import Stat
from scipy.signal import find_peaks


class GBTStatus:
    def __init__(self, pos, GBT, GBT_base, GBT_CD_coefficient):
        self.GBT_pars = GBT
        self.GBT_base = GBT_base
        self.GBT_CD_coefficient = GBT_CD_coefficient

        self.BC = None  # threshold of the BC border.
        self.CD = None  # threshold of the CD border.

        self.pos = pos

    def __GBT_borders(self, pos: str):
        """
        Value of the GBT BC and CB borders.
        :param pos: str; the monitored position.
        """
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

        gbt_bc = self.GBT_pars["GBT_" + key + "_BC"]
        gbt_cd = self.GBT_pars["GBT_" + key + "_CD"]
        base = self.GBT_base

        temp_bc = base + 0.25 * gbt_bc
        if temp_bc > gbt_bc:
            self.BC = gbt_bc
        else:
            self.BC = temp_bc

        CD_coef = self.GBT_CD_coefficient

        self.CD = CD_coef * gbt_cd

    def OA_status(self, OA: float):
        """
        The health status evaluated from OA.
        :param OA: float. Characteristic OA of the inspected duration.
        :return: float, str; OA, healthy status.
        """
        self.__GBT_borders(self.pos)

        if OA < self.BC:
            status = 'B'
        elif OA >= self.CD:
            status = 'D'
        else:
            status = 'C'

        ratio_BC = OA / self.BC
        ratio_CD = OA / self.CD

        return OA, status, self.BC, self.CD, ratio_BC, ratio_CD


class Shock:
    def __init__(self, shock_snr_th, sr, window_ENBW, GBT, shock_frame_length, shock_hop_length):
        self.shock_snr_th = shock_snr_th
        self.sr = sr
        self.shock_frame = shock_frame_length
        self.shock_hop = shock_hop_length
        self.window_ENBW = window_ENBW
        self.GBT = GBT

    def shock_finder(self, raw):
        st_tools = Stat(self.sr, self.window_ENBW, self.GBT)

        rms = st_tools.rms(raw)[0]

        tail = len(raw) % self.shock_frame
        if tail > 0:
            raw = raw[0: -tail]

        raw = raw.reshape([-1, self.shock_frame])

        crest_global_clip = st_tools.crest(raw, rms).flatten()
        crest_partial_clip = st_tools.crest(raw).flatten()

        crest_idx1 = np.argwhere(crest_global_clip > self.shock_snr_th).flatten() * self.shock_frame
        crest_idx2 = np.argwhere(crest_partial_clip > self.shock_snr_th).flatten() * self.shock_frame
        clip_idx = np.array([x for x in crest_idx1 if x in crest_idx2])

        raw = raw.flatten()

        max_shock = 0
        if len(clip_idx):
            if_shock = True
            for idx in clip_idx:
                temp_max = np.max(np.abs(raw[idx: idx + self.shock_frame]))
                if max_shock < temp_max:
                    max_shock = temp_max
        else:
            if_shock = False

        shock_ratio = max_shock / rms

        return if_shock, max_shock, shock_ratio, clip_idx


class SpecAnalysis:
    def __init__(self, pos, sr, spec_snr, delta_freq, harmonic_orders, minN_rms, base_freqs, GBT, window_ENBW):

        self.delta_freq = delta_freq  # searching frequency error ranges of the given frequency at low-speed end.
        self.orders = harmonic_orders  # maximum harmonic orders to inspect.
        self.pos = pos
        self.line_snr = spec_snr  # significance of the emission line.
        self.sr = sr
        self.minN_rms = minN_rms  # mininum number of spectral data points to calculate rms.
        self.GBT = GBT
        self.window_ENBW = window_ENBW

        self.base_freqs = base_freqs

    def find_spectral_line(self, target_freq: float, spec_line: np.ndarray, freq_array: np.ndarray, rms: float):
        """
        To find if there is the target spectral line in the given spectrum.
        :param freq_array: frequency array corresponding to the spec array.
        :param spec_line: spectrum to search the target spectral line.
        :param rms: local rms of the spectrum.
        :param target_freq: frequency of the target spectral line.
        :return: spctral line index, frequency, amplitude, and snr (all values are set to zero if there is no such line).
        """
        peak_idxs, _ = find_peaks(spec_line)
        peak_amps = spec_line[peak_idxs]
        which_peaks = np.argwhere(peak_amps >= (self.line_snr * rms)).flatten()

        peak_candi_id = peak_idxs[which_peaks]
        peak_candi_freq = freq_array[peak_candi_id]

        if len(peak_candi_freq):
            which_candi = np.argmin(np.abs(peak_candi_freq - target_freq))
            peak_freq = peak_candi_freq[which_candi]
            peak_id = peak_candi_id[which_candi]
            peak_amp = spec_line[peak_id]
            peak_snr = peak_amp / rms
        else:
            peak_freq = 0
            peak_id = 0
            peak_amp = 0
            peak_snr = 0

        return peak_id, peak_freq, peak_amp, peak_snr

    def spec_clip(self, full_spec: np.ndarray, target_freq: float, rotat_freq: float):
        """
        Get the spectrum clips for spectral-line searching and rms calculation.
        :param rotat_freq: rotational frequency.
        :param full_spec: np.ndarray. Spectrum of [0 Hz, sr//2 Hz]
        :param target_freq: frequency of the emission line for searching
        :return: rms: float, local rms to calculate SNR.
                 spectrum_clip: spectrum clip to search for the targe line.
                 freq_array_clip: frequency array clip to search for the targe line.
                 idx_low: start index of the spectrum clip in the full spectrum.
        """

        freq_array = np.linspace(0, self.sr // 2, len(full_spec))

        # Get spectrum clip for target-line searching.
        delta_freq = self.delta_freq

        tar_freq_low = (rotat_freq - delta_freq) * target_freq / rotat_freq
        tar_freq_high = (rotat_freq + delta_freq) * target_freq / rotat_freq

        if tar_freq_low < 0:
            tar_freq_low = 0

        idx_low = np.argwhere(freq_array >= tar_freq_low).flatten()[0]
        idx_high = np.argwhere(freq_array <= tar_freq_high).flatten()[-1]

        if idx_low:
            spectrum_clip = full_spec[idx_low - 1: idx_high + 1]
            freq_array_clip = freq_array[idx_low - 1: idx_high + 1]
        else:
            spectrum_clip = full_spec[idx_low: idx_high + 1]
            freq_array_clip = freq_array[idx_low: idx_high + 1]

        # Calculate rms.
        N = idx_high - idx_low
        if N >= self.minN_rms:
            rms_clip = spectrum_clip
        else:
            delta_id = (self.minN_rms - N) / 2
            if idx_low - delta_id <= 0:
                rms_clip = full_spec[0: self.minN_rms + 1]
            else:
                rms_clip_id_low = int(np.floor(idx_low - delta_id))
                rms_clip_id_high = int(np.ceil(idx_high + delta_id))
                rms_clip = full_spec[rms_clip_id_low: rms_clip_id_high]

        st_tools = Stat(self.sr, self.window_ENBW, self.GBT)
        rms = st_tools.rms(rms_clip)[0]

        return rms, spectrum_clip, freq_array_clip, idx_low

    def find_harmonics(self, full_spec: np.ndarray, base_freq: float, rotat_freq: float):
        """
        Extract harmonics from the spectrum, if there is any.
        :param full_spec: np.ndarray. Spectrum of [0 Hz, sr//2 Hz]
        :param base_freq: base frequency of defect at ValidatingData Hz
        :param rotat_freq: rotational frequency
        :return:
        """

        harmonic_matrix = np.zeros([self.orders, 5])
        freq_array = np.linspace(0, self.sr // 2, len(full_spec))

        for n in range(self.orders):
            order = n + 1
            target_frequency = rotat_freq * base_freq * order
            rms, spectrum_clip, freq_array_clip, idx_low = self.spec_clip(full_spec, target_frequency, rotat_freq)
            peak_idx, peak_freq, peak_amp, peak_snr = \
                self.find_spectral_line(target_frequency, spectrum_clip, freq_array_clip, rms)
            peak_idx = peak_idx + idx_low - 1
            if peak_idx and peak_freq and peak_amp:
                harmonic_matrix[n] = order, peak_idx, freq_array[peak_idx], full_spec[peak_idx], peak_snr

        no_detection_id = np.argwhere(harmonic_matrix[:, 0] == 0).flatten()
        harmonic_matrix = np.delete(harmonic_matrix, no_detection_id, axis=0)

        return harmonic_matrix
