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
from core.algorithm_library.PowerStation.Statistics import Stat


class Plot:
    def __init__(self, configs):
        for key, val in configs.items():
            setattr(self, key, val)

    def wave_plot(self, raw, pos):
        st_tools = Stat(self.sr, self.window_ENBW)

        data = raw
        rms = st_tools.rms(data)

        time_axis = np.arange(len(data)) / self.sr
        fig = plt.figure(figsize=(15, 5))
        plt.plot(time_axis, data, lw=0.7, color='royalblue')
        plt.plot([time_axis[0], time_axis[-1]], np.ones(2) * rms * 5, color='red', ls='dashed',
                 lw=2, label=r'5$\sigma$')
        plt.plot([time_axis[0], time_axis[-1]], -np.ones(2) * rms * 5, color='red', ls='dashed',
                 lw=2)

        plt.rcParams["font.sans-serif"] = ["SimHei"]  # 设置字体
        plt.rcParams["axes.unicode_minus"] = False
        plt.xticks(fontsize='large')
        plt.yticks(fontsize='large')
        plt.xlabel(r'时间 (s)', fontsize='x-large')
        plt.ylabel(r'加速度 (m/s$^2$)', fontsize='x-large')
        plt.title(self.equipment_id + ' ' + self.position_mapping[pos] + '波形', fontsize='xx-large')
        plt.legend(loc='best', framealpha=0.7, fontsize='x-large')
        fig_path = os.path.join(self.savedir, pos + '_wave.png')
        plt.savefig(fig_path)
        plt.clf()
        plt.close()
        gc.collect()

        return fig_path

    def spec_plot(self, spec, defect_matrices, plot_upper_freq, pos):
        freq_axis = np.linspace(0, self.sr // 2, len(spec))
        fig = plt.figure(figsize=(15, 5))
        plt.plot(freq_axis, spec, lw=0.7, color='royalblue')

        if len(defect_matrices.keys()):
            for key, values in defect_matrices.items():
                cl = self.char_freq_info[key][2]
                location = self.char_freq_info[key][3]
                order = values[:, 0]
                freq = values[:, 2]
                amp = values[:, 3]
                plt.scatter(freq, amp, marker='x', facecolors=cl, linewidths=2, s=100, label=location)
                for i in range(len(order)):
                    plt.text(freq[i], amp[i]*1.05, str(int(order[i])), color=cl)

                for key1 in self.char_freq_info.keys():
                    for j in range(self.harmonic_orders):
                        plt.plot(np.ones(2) * (j+1) * self.char_freq_info[key1][0]*self.rotat_freq, [0, np.max(spec)],
                                 lw=0.1, color=self.char_freq_info[key1][2], ls='dashed')
        else:
            pass

        plt.xlim([0, plot_upper_freq])
        plt.rcParams["font.sans-serif"] = ["SimHei"]  # 设置字体
        plt.rcParams["axes.unicode_minus"] = False
        plt.xticks(fontsize='large')
        plt.yticks(fontsize='large')
        plt.xlabel(r'频率 (Hz)', fontsize='x-large')
        plt.ylabel(r'加速度 (m/s$^2$)', fontsize='x-large')
        plt.title(self.position_mapping[pos] + '包络解调谱', fontsize='xx-large')
        plt.legend(loc='best', framealpha=0.7, fontsize='x-large')
        fig_path = os.path.join(self.savedir, pos + '_envspec.png')
        plt.savefig(fig_path)
        plt.clf()
        plt.close()
        gc.collect()

        return fig_path

