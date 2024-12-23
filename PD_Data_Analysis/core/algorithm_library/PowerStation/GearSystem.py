#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
import os
import numpy as np
from core.algorithm_library.PowerStation.Statistics import Stat
from core.algorithm_library.PowerStation.Diagnosis import Diagnosis
from core.algorithm_library.PowerStation.DataReduction import DataRe
from core.algorithm_library.PowerStation.Plot import Plot
from core.algorithm_library.PowerStation.VibAnalysis import Harmonics


class Gears:
    def __init__(self, crud_instance, **configs):
        self.crud = crud_instance
        self.positions_config = configs

        for key, val in configs.items():
            setattr(self, key, val)

    def __update_algorithm_configs(self, equipment_id: str):
        """
        根据设备和通道更新参数
        :param equipment_id: 设备号
        :return: 无
        """
        self.equipment_id = equipment_id
        self.algorithm_config = self.crud.get_monitor_config(user='algorithm', equipment_id=equipment_id).__dict__

        for key, val in self.algorithm_config.items():
            setattr(self, key, val)

        self.savedir = os.path.join(self.crud.database_root, equipment_id)

    def __update_position_configs(self, datapack: dict):
        """
        读入data_pack中的测点参数
        """
        self.pos_config = self.positions_config[datapack["position"]]
        for key1, val1 in self.pos_config.items():
            setattr(self, key1, val1)

        for key, val in datapack.items():
            if key != 'raw':
                setattr(self, key, val)
            else:
                pass

    def rt_diagnosis(self, **data_pack):
        """
        对一组齿轮进行故障诊断，仅包括主动轮和从动轮

        """
        self.__update_algorithm_configs(data_pack["equipment_id"])
        self.__update_position_configs(data_pack)

        raw = data_pack["raw"]

        dr_tools = DataRe(self.sr)
        st_tools = Stat(self.sr, self.window_ENBW)
        configs = self.__dict__
        diag_tools = Diagnosis(configs)

        # 振动总值，振动总值评级，即部件健康评级
        OA = st_tools.oa(raw, self.OA_freq_range["high"], self.OA_freq_range["low"])
        OA_status = diag_tools.oa_status(OA)

        # 谐波特征提取
        # 求包络谱
        env_spec = self.__harm_spec(raw)
        # 获取转频（Hz）
        rotat_freq = dr_tools.avg_rotat_freq(self.rotat_freq)
        # 获取谐波信息
        defect_matrices = self.__defect_detection(env_spec, rotat_freq)

        gear_defects = diag_tools.gear_defects(OA, defect_matrices, raw)

        # 存图
        configs = self.__dict__
        pt_tools = Plot(configs)

        # wave_fig_path = pt_tools.wave_plot(raw, data_pack["position"])
        # spec_fig_path = pt_tools.spec_plot(env_spec, defect_matrices, self.plot_upper_freq, data_pack["position"])

        return {
            "OA": OA,
            "health_status": OA_status,
            "gear_defects": gear_defects,
            # "wave_fig_path": wave_fig_path,
            # "spec_fig_path": spec_fig_path,
            # "defect_matrices": defect_matrices
        }

    def __harm_spec(self, raw: np.ndarray):
        """-
        计算包络谱
        :param raw: 一维数组，仅进行过归一化的原始振动数据。
        :return: 包络谱
        """
        dr_tools = DataRe(self.sr)
        filtered = dr_tools.butterworth_filter(raw, self.envelope_band["low"], self.envelope_band["high"],
                                               self.envelope_band["order"])
        env = dr_tools.hilbert_envelope(filtered)
        env_spec = dr_tools.get_spectrum(env)
        return env_spec

    def __defect_detection(self, spec: np.ndarray, rotat_freq: float):
        """
        特征频率相关的缺陷检测
        :param spec: 包络谱
        :param rotat_freq: 转频
        :return: 字典，各特征频率和转频（若有）对应的缺陷矩阵
        """
        sp_tools = Harmonics(self.sr, self.delta_freq, self.minN_rms, self.window_ENBW, self.harmonic_orders,
                             self.snr_th_1st)

        defect_matrices = {}
        for base_type, base_info in self.char_freq_info.items():
            char_freq = base_info[0]
            spec_snr_th = base_info[1]
            harmonic_matrix = sp_tools.find_harmonics(spec, char_freq, rotat_freq, spec_snr_th)
            if len(harmonic_matrix):
                defect_matrices[base_type] = harmonic_matrix
            else:
                pass

        return defect_matrices
