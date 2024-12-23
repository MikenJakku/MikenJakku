#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
import os.path
import gc
import numpy as np
import matplotlib.pyplot as plt
from core.algorithm_library.WT_Project.DataReduction import DataRe


class Plot:
    def __init__(self, save_dir, raw, wave_bp_low, wave_bp_high, sr, pos, position_mapping, freq_upper_limit, channel_name,
                 defect_matrices, wave_std, statistic_NL_mapping):
        self.raw = raw
        self.wave_bp_low = wave_bp_low
        self.wave_bp_high = wave_bp_high
        self.sr = sr
        self.pos = pos
        self.position_mapping = position_mapping[self.pos]
        self.freq_upper_lim = freq_upper_limit[self.pos]
        self.channel_name = channel_name
        self.defect_matrices = defect_matrices
        self.wave_std = wave_std
        self.statistic_NL_mapping = statistic_NL_mapping

        self.bp_order = 2
        self.save_dir = save_dir

    def wave_plot(self, raw):
        dr_tools = DataRe(self.sr)
        data = dr_tools.butterworth_filter(raw, self.wave_bp_low, self.wave_bp_high, self.bp_order)[
               10 * self.sr: -10 * self.sr]
        time_axis = np.arange(len(data)) / self.sr
        fig = plt.figure(figsize=(15, 5))
        plt.plot(time_axis, data, lw=0.7, color='royalblue')
        plt.plot([time_axis[0], time_axis[-1]], np.array([self.wave_std, self.wave_std]) * 5, color='red', ls='dashed',
                 lw=2, label=r'5$\sigma$')
        plt.plot([time_axis[0], time_axis[-1]], -np.array([self.wave_std, self.wave_std]) * 5, color='red', ls='dashed',
                 lw=2)

        plt.rcParams["font.sans-serif"] = ["SimHei"]  # 设置字体
        plt.rcParams["axes.unicode_minus"] = False
        plt.xticks(fontsize='large')
        plt.yticks(fontsize='large')
        plt.xlabel(r'时间 (s)', fontsize='x-large')
        plt.ylabel(r'加速度 (m/s$^2$)', fontsize='x-large')
        plt.title(self.position_mapping + '波形', fontsize='xx-large')
        plt.legend(loc='best', framealpha=0.7, fontsize='x-large')
        fig_path = os.path.join(self.save_dir, self.channel_name + '_' + self.pos + '_wave.png')
        plt.savefig(fig_path)
        plt.clf()
        plt.close()
        gc.collect()

        return fig_path

    def spec_plot(self, spec):
        info_map = {"BPFO": ["#ffa600", "外滚道特征频率"],
                    "BPFI": ["#ff6361", "内滚道特征频率"],
                    "BSF": ["#bc5090", "滚动子特征频率"],
                    "FTF_i": ["#58508d", "保持架特征频率"],
                    "rotation": ["#003f5c", "转频"]}

        freq_axis = np.linspace(0, self.sr // 2, len(spec))
        fig = plt.figure(figsize=(15, 5))
        plt.plot(freq_axis, spec, lw=0.7, color='royalblue')

        if len(self.defect_matrices.keys()):
            for key, values in self.defect_matrices.items():
                cl = info_map[key][0]
                location = info_map[key][1]
                freq = values[:, 2]
                amp = values[:, 3]
                plt.scatter(freq, amp, marker='x', facecolors=cl, linewidths=2, s=100, label=location)
        else:
            pass

        # plt.xlim([0, 200])
        plt.xlim([0, self.freq_upper_lim])

        plt.rcParams["font.sans-serif"] = ["SimHei"]  # 设置字体
        plt.rcParams["axes.unicode_minus"] = False
        plt.xticks(fontsize='large')
        plt.yticks(fontsize='large')
        plt.xlabel(r'频率 (Hz)', fontsize='x-large')
        plt.ylabel(r'加速度 (m/s$^2$)', fontsize='x-large')
        plt.title(self.position_mapping + '包络解调谱', fontsize='xx-large')
        plt.legend(loc='best', framealpha=0.7, fontsize='x-large')
        fig_path = os.path.join(self.save_dir, self.channel_name + '_' + self.pos + '_envspec.png')
        plt.savefig(fig_path)
        plt.clf()
        plt.close()
        gc.collect()

        return fig_path

    def trending_plot(self, features):
        for ft, values in features.items():
            data = values[1]
            date_ax = np.arange(len(data))
            fig = plt.figure(figsize=(15, 5))
            plt.plot(date_ax, data, lw=1, color='royalblue')
            plt.rcParams["font.sans-serif"] = ["SimHei"]  # 设置字体
            plt.rcParams["axes.unicode_minus"] = False
            plt.xticks(fontsize='large')
            plt.yticks(fontsize='large')
            plt.xlabel(r'日', fontsize='x-large')
            plt.ylabel(r'特征值', fontsize='x-large')
            plt.title(self.position_mapping + self.statistic_NL_mapping[ft] + "长期趋势", fontsize='xx-large')
            plt.legend(loc='best', framealpha=0.7, fontsize='x-large')
            fig_path = os.path.join(self.save_dir, self.channel_name + '_' + self.pos + '_' + ft + '_trending.png')
            plt.savefig(fig_path)
            plt.clf()
            plt.close()
            gc.collect()
