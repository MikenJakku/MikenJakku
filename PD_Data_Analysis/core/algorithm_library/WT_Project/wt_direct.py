#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
from core.algorithm_library.WT_Project.Statistics import Stat
from core.algorithm_library.WT_Project.DataReduction import DataRe
from core.algorithm_library.WT_Project.VibAnalysis import GBTStatus, Shock, SpecAnalysis
from core.algorithm_library.WT_Project.Trend import Trending
from core.algorithm_library.WT_Project.Diagnosis import Diagnosis
from core.algorithm_library.WT_Project.Plot import Plot
from core.algorithm_library.WT_Project.HumanFriendly import HumanFriendly
import numpy as np
import matplotlib.pyplot as plt
import os
import pandas as pd
import gc


class WTDirect:
    def __init__(self, crud_instance, **channel_config):
        self.crud = crud_instance
        self.channel_config = channel_config
        for key, val in channel_config.items():
            setattr(self, key, val)

    # ------------------ real-time feature extraction ------------------#
    def __update_configs(self, equipment_id, channel_name, sr):
        """
        根据设备和通道更新参数
        :param equipment_id: 设备号
        :param channel_name: 通道号
        :param sr: 采样率
        :return: 无
        """
        setattr(self, "equipment_id", equipment_id)
        setattr(self, "channel_name", channel_name)
        setattr(self, "sr", sr)
        # self.crud.equipment_register(self.equipment_id)

        self.algorithm_config = self.crud.get_monitor_config(user='algorithm', equipment_id=self.equipment_id).__dict__

        for key, val in self.algorithm_config.items():
            setattr(self, key, val)

        self.channel_config = self.algorithm_config[channel_name]
        for key1, val1 in self.channel_config.items():
            setattr(self, key1, val1)

        self.save_dir = os.path.join(self.crud.database_root, self.equipment_id)

        if self.position.startswith("shaft"):
            self.char_frequencies = self.algorithm_config["char_frequencies"]["shaft"]
        elif self.position.startswith("stator"):
            self.char_frequencies = self.algorithm_config["char_frequencies"]["stator"]
        elif self.position.startswith("generator"):
            self.char_frequencies = self.algorithm_config["char_frequencies"]["generator"]
        elif self.position.startswith("gearbox_input"):
            self.char_frequencies = self.algorithm_config["char_frequencies"]["gearbox_input"]
        elif self.position.startswith("gearbox_planetary"):
            self.char_frequencies = self.algorithm_config["char_frequencies"]["gearbox_planetary"]
        elif self.position.startswith("gearbox_mid"):
            self.char_frequencies = self.algorithm_config["char_frequencies"]["gearbox_mid"]
        elif self.position.startswith("gearbox_output"):
            self.char_frequencies = self.algorithm_config["char_frequencies"]["gearbox_output"]
        else:
            self.char_frequencies = {"rotation": 1}

    # ------------------ real-time feature extraction ------------------#
    def rt_features(self, raw: np.ndarray, freq_rpm_high: np.ndarray, freq_rpm_low: np.ndarray, datetime: str,
                    equipment_id, channel_name, sr: int):
        """
        - 针对每3分钟数据提取统计特征;
        - 筛选并保存用于生成（当日）监测报告的原始数据;
        - 保存用于长期趋势监测的统计特征
        :param raw: 一维数组，仅进行过归一化的原始振动数据。
        :param freq_rpm_high: 一维数组，高速端转速
        :param freq_rpm_low: 一维数组，低速端转速
        :param datetime: 数据采集时间 yyyymmddhhmmss
        :param equipment_id:str, 设备编号
        :param channel_name:str，通道号
        :param sr: int, 采样率
        :return: None
        """
        self.__update_configs(equipment_id, channel_name, sr)

        dr_tools = DataRe(self.sr)
        jd = dr_tools.to_julian(datetime)

        # 统计特征
        features = self.__rt_features(raw)
        # 存储统计特征
        statistical_values_pth = os.path.join(self.save_dir, self.channel_name+'_statistics.csv')
        if os.path.exists(statistical_values_pth):
            df = pd.read_csv(statistical_values_pth, index_col=0)
            df.loc[jd] = {"OA": features["OA"], "pp":features["pp"], "kurtosis": features["kurtosis"],
                          "skewness": features["skewness"], "crest": features["crest"]}
            df.to_csv(statistical_values_pth)
        else:
            data = pd.DataFrame(np.array([[features["OA"], features["pp"], features["skewness"],
                                           features["kurtosis"], features['crest']]]), index=[jd],
                                columns=["OA", "pp", "skewness", "kurtosis", "crest"])
            data.to_csv(statistical_values_pth)

        # 数据筛选
        self.__data_selection(raw, freq_rpm_high, freq_rpm_low, datetime)

        return 0

    def __data_selection(self, raw: np.ndarray, freq_rpm_high: np.ndarray, freq_rpm_low: np.ndarray, datetime: str):
        """
        诊断用数据筛选。
        :param raw: 一维数组，仅进行过归一化的原始振动数据。
        :param freq_rpm_high: 一维数组，高速端转速
        :param freq_rpm_low: 一维数组，低速端转速
        """

        data = {
            'raw': raw,
            'freq_rpm_low': freq_rpm_low,
            'freq_rpm_high': freq_rpm_high,
            'datetime': datetime
        }

        if np.sum(freq_rpm_high) > 1e-4:
            freq_rpm = freq_rpm_high
        else:
            freq_rpm = freq_rpm_low

        freq_avg = np.average(freq_rpm)
        freq_std = np.std(freq_rpm)

        try:
            freq_rpm_previous = self.crud.data_read_ordinary(self.equipment_id, self.channel_name+'_previous_rpm')
            if freq_std < np.std(freq_rpm_previous):
                self.crud.data_storage_ordinary(self.equipment_id, self.channel_name+'_previous_rpm', freq_rpm)
                self.crud.data_storage_ordinary(self.equipment_id, self.channel_name, data)
            elif freq_std == np.std(freq_rpm) and freq_avg > np.average(freq_rpm_previous):
                self.crud.data_storage_ordinary(self.equipment_id, self.channel_name+'_previous_rpm', freq_rpm)
                self.crud.data_storage_ordinary(self.equipment_id, self.channel_name, data)
            else:
                pass
        except FileNotFoundError:
            self.crud.data_storage_ordinary(self.equipment_id, self.channel_name + '_previous_rpm', freq_rpm)
            self.crud.data_storage_ordinary(self.equipment_id, self.channel_name, data)

    def __rt_features(self, raw: np.ndarray):
        """
        统计特征计算
        :param raw: 一维数组，仅进行过归一化的原始振动数据
        :return: 字典，统计特征名称及对应值
        """
        st_tools = Stat(self.sr, self.window_ENBW, self.GBT)
        oa, pp, avg, std, skew, kurt, crest = st_tools.oa_and_statistics(raw, self.position)
        rt_ft = {
            "OA": oa,
            "pp": pp,
            "avg": avg,
            "std": std,
            "skewness": skew,
            "kurtosis": kurt,
            "crest": crest
        }
        return rt_ft

    def __rt_shock(self, raw: np.ndarray):
        """
        判断一段时域信号是否存在冲击特征；计算最大冲击的幅值和信噪比
        :param raw: 一维数组，仅进行过归一化的原始振动数据
        :return: 字典，是否存在冲击、最大冲击幅值、最大冲击的信噪比
        """
        shock_tools = Shock(self.shock_snr_th, self.sr, self.window_ENBW, self.GBT,
                            self.shock_frame_length, self.shock_hop_length)
        if_shock, max_shock, shock_ratio, clip_idx = shock_tools.shock_finder(raw)
        result = {
            "if_shock": if_shock,
            "shock_maximum": max_shock,
            "shock_snr": shock_ratio
        }

        return result

    def __rt_viewer_wave_spec(self, raw: np.ndarray):
        """
        提供绘图所需数据点的横坐标、数值
        :param raw: 一维数组，仅进行过归一化的原始振动数据
        :return: 字典。绘制波形图、频谱图的数据点
        """
        dr_tools = DataRe(self.sr)
        ds, n = dr_tools.down_sampling(raw, self.down_sampling_rate)
        ds_sr = self.sr // self.down_sampling_rate

        tx = np.arange(len(ds)) / ds_sr

        spec = dr_tools.get_spectrum(ds)
        fx = np.linspace(0, ds_sr // 2, len(spec))

        waveform = np.array([tx, ds])
        spectrum = np.array([fx, spec])

        result = {
            "waveform": waveform,
            "spectrum": spectrum
        }

        return result

    # ------------------ real-time feature extraction ------------------#

    def diagnosis_report(self, datetime, equipment_id, channel_name, sr:int):
        """
        针对用于生成监测报告的3分钟数据，进行：
        - 统计特征提取   - 冲击判断   - 健康等级评估  - 缺陷检测
        - 故障诊断
        - 特征图谱绘制和存储
        - 监测报告所需信息的自然语言描述。
        :param datetime: 数据采集时间 yyyymmddhhmmss
        :param equipment_id:str, 设备编号
        :param channel_name:str，通道号
        :param sr: int,采样率
        :return: 字典：诊断结果、对应检测报告中的自然语言表述、特征图谱存储路径
        """
        self.__update_configs(equipment_id, channel_name, sr)

        data = self.crud.data_read_ordinary(self.equipment_id, self.channel_name)
        raw = data["raw"]
        freq_rpm_low = data["freq_rpm_low"]
        freq_rpm_high = data["freq_rpm_high"]

        # 统计特征
        features = self.__rt_features(raw)

        # 波形冲击特征
        shock = self.__rt_shock(raw)

        # 国标健康分级
        health_status = self.__health_status(features["OA"])

        # 缺陷频率特征检测
        env_spec = self.__harm_spec(raw)
        avg_freq_rpm = self.__rotational_frequency(freq_rpm_high, freq_rpm_low)
        defect_matrices = self.__defect_detection(env_spec, avg_freq_rpm)

        # 缺陷诊断结论
        diagnosis_rst = self.__defect_diagnose(defect_matrices)

        # 绘制特征图谱并保存
        plot_tools = Plot(self.save_dir, raw, self.wave_bp_low, self.wave_bp_high, self.sr, self.position,
                          self.position_mapping, self.plot_freq_upper_limit, self.channel_name, defect_matrices, features["std"],
                          self.statistic_NL_mapping)

        wave_fig_path = plot_tools.wave_plot(raw)
        spec_fig_path = plot_tools.spec_plot(env_spec)

        # 长期趋势监测
        trending_rst, trending_nl, trend_fig_pth = self.trending(datetime)

        full_results = {
            "features": features,
            "shock": shock,
            "health_status": health_status,
            "defect_harmonics": defect_matrices,
            "diagnosis_rst": diagnosis_rst,
            "fig_paths": {
                "wave_fig": wave_fig_path,
                "spec_fig": spec_fig_path,
                "trend_fig": trend_fig_pth,
            },
            "bandpass": {"low": self.spec_bp_low, "high": self.spec_bp_high}
        }
        # 删除之前的数据
        self.crud.data_delete_ordinary(self.equipment_id, self.channel_name)
        self.crud.data_delete_ordinary(self.equipment_id, self.channel_name + '_previous_rpm')

        # 自然语言表述上述诊断结果
        nl_tools = HumanFriendly(self.position, full_results, self.health_status_mapping, self.position_mapping,
                                 self.wave_comment_mapping, self.defect_freq_mapping, self.spec_comment_mapping,
                                 self.trending_comment_mapping, self.statistic_NL_mapping, self.rotational_defects_mapping,
                                 self.defect_level_mapping, self.maintenance_NL_mapping)
        rst_nl = nl_tools.nature_language()
        rst_nl["trendingNL"] = trending_nl["trendingNL"]

        # results["trending"] = trending_rst
        results = {
            "features": features,
            "fig_paths": {
                "wave_fig": wave_fig_path,
                "spec_fig": spec_fig_path,
                "trend_fig": trend_fig_pth,
            },
            "bandpass": {"low": self.spec_bp_low, "high": self.spec_bp_high},
            "position": self.position_mapping[self.position]

        }

        return results, rst_nl

    def __health_status(self, OA: float):
        """
        根据国标进行的健康等级评估
        :param OA: float，振动总值
        :return: 字典。振动总值、健康等级、B/C和C/D区域边界值，振动总值相对于两边界值的比值
        """
        gbt_tools = GBTStatus(self.position, self.GBT, self.GBT_base, self.GBT_CD_coefficient)
        OA, status, BC, CD, ratio_BC, ratio_CD = gbt_tools.OA_status(OA)

        result = {
            "OA": OA,
            "status": status,
            "BC": BC,
            "CD": CD,
            "ratio_BC": ratio_BC,
            "ratio_CD": ratio_CD
        }

        return result

    def __harm_spec(self, raw: np.ndarray):
        """
        计算包络谱
        :param raw: 一维数组，仅进行过归一化的原始振动数据。
        :return: 包络谱
        """
        dr_tools = DataRe(self.sr)
        filtered = dr_tools.butterworth_filter(raw, self.spec_bp_low, self.spec_bp_high, 2)[10*self.sr: -10*self.sr]
        env = dr_tools.hilbert_envelope(filtered)
        env_spec = dr_tools.get_spectrum(env)
        return env_spec

    def __rotational_frequency(self, rpm_high: np.ndarray, rpm_low: np.ndarray):
        """
        转频均值
        :param rpm_low: 传感器直接读出的低速端转频数组
        :return: 高速或低速端转频均值
        """

        freq_rpm = rpm_low / self.rpm_pulse

        avg_freq_rpm = np.average(freq_rpm)

        return avg_freq_rpm

    def __defect_detection(self, spec: np.ndarray, freq_rpm: float):
        """
        特征频率相关的缺陷检测
        :param spec: 包络谱
        :param freq_rpm: 转速
        :return: 字典，各特征频率和转频（若有）对应的缺陷矩阵
        """

        sp_tools = SpecAnalysis(self.position, self.sr, self.spec_snr_th, self.delta_freq, self.harmonic_orders,
                                self.minN_rms, self.char_frequencies, self.GBT_base, self.window_ENBW)

        defect_matrices = {}
        for base_type, base_freq in self.char_frequencies.items():
            harmonic_matrix = sp_tools.find_harmonics(spec, base_freq, freq_rpm)
            if len(harmonic_matrix):
                defect_matrices[base_type] = harmonic_matrix
            else:
                pass

        return defect_matrices

    def __defect_diagnose(self, defect_matrices: dict):
        """
        根据缺陷矩阵，诊断缺陷类型
        :param defect_matrices:
        :return: 字典：对应特征值的缺陷类型和严重等级
        """
        dg_tools = Diagnosis(self.surface_defect_dscrp, self.defect_snr_minor, self.defect_snr_obv, self.defect_snr_vital,
                             self.defect_level, self.rotational_defect_types)

        diagnose_rst = {}

        for type, harmonic in defect_matrices.items():
            if type == 'rotation':
                defect, level = dg_tools.rotational_defect_diagnosis(harmonic)
                if level is None:
                    pass
                else:
                    diagnose_rst[type] = {"defect": defect, "level": level}
            else:
                defect, level = dg_tools.surface_defect_level(harmonic)
                diagnose_rst[type] = {"defect": defect, "level": level}

        return diagnose_rst

    # ------------------ real-time feature extraction ------------------#
    def trending(self, datetime: str):
        """
        - 对各统计特征的长期趋势监测（判断是否存在趋势性）
        - 绘制趋势图谱
        - 监测报告所需的相关自然语言描述
        :param datetime: 长期趋势监测截止时间，精确到秒
        :return:字典；各统计值的长期检测数据是否存在趋势、对应的自然语言描述、长期趋势监测图谱路径
        """
        trending_tools = Trending()
        rst = {}

        dr_tools = DataRe(self.sr)
        jd = dr_tools.to_julian(datetime)
        trend_start = jd - self.trending_period

        features_all = pd.read_csv(os.path.join(self.save_dir, self.channel_name+'_statistics.csv'), index_col=0)
        features = features_all[str(trend_start):]
        real_start = float(features.index[0])
        if np.abs(trend_start - real_start) >= 1:
            rst_nl = {"trendingNL": '监测时间过短，请监测'+str(self.trending_period)+"天以上再进行长期趋势判断。"}
            fig_path = None
        else:
            fig = plt.figure(figsize=(15, 5))

            cmap = {"OA": '#003f5c',
                    "pp": '#ffa600',
                    "kurtosis": "#58508d",
                    "skewness": "#bc5090",
                    "crest": "#ff6361"}

            for key in features:
                values = features[key]
                trend_status = trending_tools.if_trend(values)
                rst[key] = trend_status
                plt.plot(values, lw=0.7, color=cmap[key], marker='s', label=self.statistic_NL_mapping[key], ms=3)

            plt.rcParams["font.sans-serif"] = ["SimHei"]  # 设置字体
            plt.rcParams["axes.unicode_minus"] = False
            plt.xticks(fontsize='large')
            plt.yticks(fontsize='large')
            plt.xlabel(r'日', fontsize='x-large')
            plt.ylabel(r'特征值', fontsize='x-large')
            plt.legend(fontsize='x-large', loc='best', framealpha=0.7)
            plt.title(self.position_mapping[self.position] + "长期趋势", fontsize='xx-large')
            fig_path = os.path.join(self.save_dir, self.channel_name + '_' + self.position + '_trending.png')
            plt.savefig(fig_path)
            plt.clf()
            plt.close()
            gc.collect()

            results = {"trending": rst}

            nl_tools = HumanFriendly(self.position, results, self.health_status_mapping, self.position_mapping,
                                     self.wave_comment_mapping, self.defect_freq_mapping, self.spec_comment_mapping,
                                     self.trending_comment_mapping, self.statistic_NL_mapping,
                                     self.rotational_defects_mapping,
                                     self.defect_level_mapping, self.maintenance_NL_mapping)
            rst_nl = nl_tools.nature_language()

        return rst, rst_nl, fig_path
