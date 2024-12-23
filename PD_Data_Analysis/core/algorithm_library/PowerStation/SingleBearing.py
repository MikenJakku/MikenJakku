#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
from core.algorithm_library.PowerStation.DataReduction import DataRe
from core.algorithm_library.PowerStation.Statistics import Stat
from core.algorithm_library.PowerStation.VibAnalysis import Harmonics
from core.algorithm_library.PowerStation.Plot import Plot
from core.algorithm_library.PowerStation.Diagnosis import Diagnosis
import numpy as np
import os


class SingleBearing:
    def __init__(self, crud_instance, **algorithm_config):
        self.crud = crud_instance
        for key, val in algorithm_config.items():
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

    def __update_position_configs(self, position_datapack: dict):
        """
        读入data_pack中的测点参数
        """
        self.position_cfg = position_datapack
        for key, val in position_datapack.items():
            if key != 'raw':
                setattr(self, key, val)
            else:
                pass

    def rt_diagnosis(self, equipment_id, **data_pack):
        """
        对一组单轴承数据进行异常诊断。包括单一方向振动数据诊断和多方向交互诊断。
        :param equipment_id: str, 设备编号
        :param data_pack: dict, 传入数据
        :return: 轴承诊断结果和测点OA评级
        """

        self.__update_algorithm_configs(equipment_id)

        diag_tools = Diagnosis(self.algorithm_config)
        # 提取传入数据的测点，将data_pack中有数据的测点key保存到with_data列表中
        with_data = []
        for key, contents in data_pack.items():
            if contents['raw'] is None:
                pass
            else:
                with_data.append(key)

        full_char_result = {}
        # 单测点处理结果
        for key_point in with_data:
            self.__update_position_configs(data_pack[key_point])
            rst = self.one_position(data_pack[key_point]["raw"], key_point)
            full_char_result[key_point] = rst

        # 部件健康评级
        health_status = diag_tools.part_OA_status(full_char_result)

        # 异常诊断
        # 整理谐波矩阵格式
        defect_matrices = diag_tools.organize_defect_matrices(full_char_result)
        rotat_matrix, half_rotat_matrix = diag_tools.rotational_matrices(defect_matrices)
        # 轴承自身异常诊断
        bearing_defects = diag_tools.bearing_defect_diagnosis(defect_matrices, rotat_matrix, half_rotat_matrix)
        # 联轴器、轴、机械整体等通过轴承频谱表现的异常诊断
        coupling_etc_defects = diag_tools.coupling_defects(rotat_matrix, half_rotat_matrix)

        results = {
                   # "pos_char_results": full_char_result,
                   'health_status': health_status,
                   'bearing_defects': bearing_defects,
                   "coupling_etc_defects": coupling_etc_defects
        }

        return results

    def one_position(self, raw: np.ndarray, pos: str):
        """
        对一个测点的数据进行振动总值计算、健康评级和谐波特征提取。
        :param raw: np.ndarray，原始振动数据
        :param pos: str, 该数据来自的测点，即数据包的键值
        :return: 测点的振动总值、振动总值评级、谐波矩阵、异常振动
        """
        dr_tools = DataRe(self.sr)
        st_tools = Stat(self.sr, self.window_ENBW)
        diag_tools = Diagnosis(self.algorithm_config)

        # 振动总值，振动总值评级
        OA = st_tools.oa(raw, self.OA_freq_range["high"], self.OA_freq_range["low"])
        OA_status = diag_tools.oa_status(OA)

        # 谐波特征提取
        # 求包络谱
        env_spec = self.__harm_spec(raw)
        # 获取平均转频（Hz）
        rotat_freq = dr_tools.avg_rotat_freq(self.rotat_freq)
        # 获取谐波信息
        defect_matrices = self.__defect_detection(env_spec, rotat_freq)

        # 存图
        configs = self.__dict__
        pt_tools = Plot(configs)

        wave_fig_path = pt_tools.wave_plot(raw, pos)
        spec_fig_path = pt_tools.spec_plot(env_spec, defect_matrices, self.plot_upper_freq, pos)

        rst = {
            "OA": OA,
            "OA_status": OA_status,
            "defect_matrices": defect_matrices,
            "wave_fig_pth": wave_fig_path,
            "spec_fig_pth": spec_fig_path
        }

        return rst

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
