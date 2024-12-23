#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
import numpy as np
from core.algorithm_library.PowerStation.Statistics import Stat
from core.algorithm_library.PowerStation.VibAnalysis import Shock


class Diagnosis:
    # def __init__(self, OA_thresholds: dict, char_freq_info: dict, surface_defect_th: dict):
    #     self.OA_thresholds = OA_thresholds
    #     self.char_freq_info = char_freq_info
    #     self.surface_defect_th = surface_defect_th

    def __init__(self, configs):
        self.configs = configs
        for key, val in self.configs.items():
            setattr(self, key, val)

    def oa_status(self, OA: float) -> str:
        """
        OA status
        :param OA: float; overall acceleration.
        :return: status
        """
        if OA < self.OA_thresholds["warning"]:
            OA_status = 'healthy'
        elif OA >= self.OA_thresholds["fatal"]:
            OA_status = 'fatal'
        else:
            OA_status = 'warning'

        return OA_status

    def part_OA_status(self, full_char_rst: dict) -> str:
        """
        Health status evaluated by OA status of the monitored part.
        :param full_char_rst: results of the extracted characteristic values of each position.
        :return: str, health status of the monitored part, "healty/warning/fatal"
        """
        OA_status = []
        for key, values in full_char_rst.items():
            OA_status.append(values["OA_status"])

        if "fatal" in OA_status:
            stat = 'fatal'
        elif "warning" in OA_status:
            stat = 'warning'
        else:
            stat = "health"

        return stat

    # --------------------------------------- #
    def organize_defect_matrices(self, full_char_rst: dict) -> dict:
        """
         Organize the defect matrices of all the positions by type for further comparison.
        :param full_rst: full results of detection.
        :param with_data: list of positions with input data
        :return:
        """
        # 将各个测点的特征提取结果格式化为
        # 特征频率名-测点-谐波信息矩阵 的字典结构
        defect_matrices = {}
        for key in self.char_freq_info.keys():
            defect_matrices[key] = {}

        for pos, rsts in full_char_rst.items():
            matrx_dict = rsts['defect_matrices']
            if len(matrx_dict):
                for key, values in matrx_dict.items():
                    defect_matrices[key][pos] = values

        return defect_matrices

    def rotational_matrices(self, defect_matrices):
        rotat_matrix = {}
        half_rotat_matrix = {}
        for key, values in defect_matrices.items():
            if key == 'rotation':
                rotat_matrix.update(defect_matrices["rotation"])
            elif key == 'half_rotation':
                half_rotat_matrix.update(defect_matrices["half_rotation"])
        return rotat_matrix, half_rotat_matrix

    def bearing_defect_diagnosis(self, defect_matrices, rotat_matrix, half_rotat_matrix) -> dict:
        defect_results = {}

        if len(defect_matrices):
            surface_defects = self.__bearing_surface_defect_diagnosis(defect_matrices)
            defect_results.update(surface_defects)
            rotating_looseness = self.__bearing_rotating_looseness(rotat_matrix, half_rotat_matrix)
            defect_results.update(rotating_looseness)

        if None in defect_results.keys():
            defect_results.pop(None)

        return defect_results

    # ----- bearing surface defects -----#
    def __bearing_surface_defect_diagnosis(self, defect_matrices: dict) -> dict:
        """
        Detect surface defects and level estimation.
        :param defect_matrices cataloged by types.
        :return: surface defect location, if there is any, and the level.
        """
        rst = {}

        for key, pos_matrices in defect_matrices.items():
            if key != 'rotation' and key != 'half_rotation' and len(pos_matrices):
                # defect_type_NL = self.char_freq_info[key][3]
                max_order = []
                max_1st_snr = []
                for pos, values in pos_matrices.items():
                    max_order.append(values[-1, 0])
                    max_1st_snr.append(values[0, -1])
                max_order = np.max(np.array(max_order))
                max_1st_snr = np.max(np.array(max_1st_snr))
                defect_level = self.__bearing_surface_defect_level(max_order, max_1st_snr)
                rst[key] = defect_level
            else:
                pass

        return rst

    def __bearing_surface_defect_level(self, max_order: int, max_1st_snr: float) -> str:
        """
        Estimate the level of surface defect.
        :param max_order: max harmonic order of the characteristic frequency
        :param max_1st_snr: max snr of the 1st order harmonic.
        :return: level of the defect
        """
        grade = np.round(max_order + max_1st_snr)
        if grade <= self.surface_defect_th["warning"]:
            status = 'minor'
        elif grade > self.surface_defect_th["fatal"]:
            status = 'fatal'
        else:
            status = 'warning'

        return status

    # ----- bearing rotating looseness -----#
    def __bearing_rotating_looseness(self, rotat_matrix: dict, half_rotat_matrix: dict) -> dict:
        defect_type = "BR1"  # "rotating_looseness"

        defect = None
        level = None

        half_positions = half_rotat_matrix.keys()
        rotat_positions = rotat_matrix.keys()
        if len(rotat_positions):
            # 如果径向有半倍转频谐波，用该谐波幅值最大的测点作为考察数据；且转频谐波阶次达阈值的可直接视为严重
            if ("RH" in half_positions) or ("RV" in half_positions):
                defect_info = {"pos": None, "half_rotat_amp": 0, "rotate_array": None}
                for pos, values in half_rotat_matrix.items():
                    if pos != 'Ax':
                        if half_rotat_matrix[pos][0][3] > defect_info["half_rotat_amp"]:
                            defect_info["pos"] = pos
                            defect_info["half_rotat_amp"] = half_rotat_matrix[pos][0][3]
                            defect_info["rotate_array"] = rotat_matrix[pos]
                rotat_order = defect_info["rotate_array"][-1, 0]
                if rotat_order >= self.rotation_loose_order_th:
                    defect = defect_type
                    level = 'fatal'
            # 如果没有半倍转频，只有径向转频，则考察最高谐波阶次，达标的认为有缺陷，等级另行判断。
            elif ("RH" in rotat_positions) or ("RV" in rotat_positions):
                max_order = 0
                rotat_array = []
                for pos, values in rotat_matrix.items():
                    if pos != 'Ax':
                        if values[-1, 0] > max_order:
                            max_order = values[-1, 0]
                            rotat_array = values
                if max_order >= self.rotation_loose_order_th:
                    defect = defect_type
                    level = self.__rotating_looseness_level(rotat_array)

        return {defect: level}

    def __rotating_looseness_level(self, rotat_array: np.ndarray) -> str:
        return "Unknown"

    # ----- couplling defects ----- #
    def coupling_defects(self, rotat_matrix: dict, half_rotat_matrix) -> dict:
        """
        Coupling defects diagnosed from bearing rotational matrix.
        """

        defects = {}
        if len(rotat_matrix):
            structural_looseness = self.__structural_looseness(rotat_matrix)
            defects.update(structural_looseness)
            pillow_block_looseness = self.__pillow_block_looseness(rotat_matrix, half_rotat_matrix)
            defects.update(pillow_block_looseness)
            coupling_parallel_misalignment = self.__coupling_parallel_misalignment(rotat_matrix)
            defects.update(coupling_parallel_misalignment)
            coupling_angular_misalignment = self.__coupling_angular_misalignment(rotat_matrix)
            defects.update(coupling_angular_misalignment)
            coupling_combined_misalignment = self.__coupling_combined_misalignment(rotat_matrix)
            defects.update(coupling_combined_misalignment)

            bent_shaft = self.__bent_shaft(rotat_matrix)
            defects.update(bent_shaft)
            unbalance = self.__unbalance(rotat_matrix)
            defects.update(unbalance)

            if None in defects.keys():
                defects.pop(None)

        return defects

    # ----- structural looseness -----#
    def __structural_looseness(self, rotat_matrix: dict) -> dict:
        """
        结构松动诊断。
        :param rotat_matrix: 各测点转频谐波矩阵字典
        :return: 是否存在结构松动缺陷、缺陷等级
        """
        defect_type = "M1"  # "structural_looseness"
        direction = self.structural_loose_direction

        defect = None
        level = None

        # 有转频谐波的点位
        positions = list(rotat_matrix.keys())

        # 在松动方向有低频分量时再继续判断是否符合松动特征
        if direction in positions:
            loose_candi_array = rotat_matrix[direction]
            # 1倍谐波分量占主导
            loose_orders = loose_candi_array[:, 0]
            loose_amps = loose_candi_array[:, 3]
            if len(loose_orders) == 1 or (
                    loose_orders[1] == 2 and loose_amps[0] / loose_amps[1] >= self.structural_loose_th):
                # 松动方向谐波幅值明显大于非松动方向
                # 如果仅松动方向发现符合上面条件的谐波，则另两个方向很弱，默认满足方向性约束
                if len(positions) == 1:
                    defect = defect_type
                    level = 'warning'
                else:
                    max_1st_amp = 0
                    for key, values in rotat_matrix.items():
                        if key is not direction:
                            amp_1st = values[0, 3]
                            if max_1st_amp <= amp_1st:
                                max_1st_amp = amp_1st
                    if loose_amps[0] / max_1st_amp >= 5:
                        defect = defect_type
                        level = 'fatal'

        return {defect: level}

    # ----- pillow block looseness ----- #
    def __pillow_block_looseness(self, rotat_matrix: dict, half_rotat_matrix: dict) -> dict:
        defect_type = "M2"  # "pillow_block_looseness"

        defect = None
        level = None

        # 提取共有测点
        pos1 = set(half_rotat_matrix.keys())
        pos2 = set(rotat_matrix.keys())

        positions = list(pos1 & pos2)

        if len(positions):
            max_half_amp = 0
            max_pos = None
            for pos in positions:
                if half_rotat_matrix[pos][0:3] > max_half_amp:
                    max_half_amp = half_rotat_matrix[pos][0, 3]
                    max_pos = pos

            snr_half_rotat = half_rotat_matrix[max_pos][0, 4]

            order_rotat = rotat_matrix[max_pos][:, 0]
            if np.max(order_rotat) >= 2:
                defect = defect_type
                level = self.__pillow_block_looseness_level(snr_half_rotat, rotat_matrix[max_pos])

        return {defect: level}

    def __pillow_block_looseness_level(self, snr_half_rotat: float, rotat_array: np.ndarray) -> str:
        return "Unknown"

    # ----- misalignment ----- #
    def __coupling_parallel_misalignment(self, rotat_matrix: dict):
        """
        Radial.
        """
        defect_type = "CP1"  # "parallel_misalignment"
        positions = rotat_matrix.keys()

        defect = None
        level = None

        for pos in positions:
            if pos != 'Ax':
                rotat_array = rotat_matrix[pos]
                if (rotat_array[-1, 0] >= 3) and (rotat_array[1, 0] == 2):
                    amp_ratio = rotat_array[1, 3] / rotat_array[0, 3]
                    if amp_ratio >= self.parallel_misalignment_th:
                        defect = defect_type
                        level = self.__coupling_parallel_misalignment_level(rotat_array[-1, 0], amp_ratio)
                    else:
                        continue

        return {defect: level}

    def __coupling_parallel_misalignment_level(self, max_order: float, amp_ratio: float):
        return "Unknown"

    def __coupling_angular_misalignment(self, rotat_matrix: dict):
        defect_type = "CP2"  # "angular_misalignment"

        defect = None
        level = None

        positions = rotat_matrix.keys()
        if ('Ax' in positions) and len(positions) > 1:
            rotat_array_ax = rotat_matrix['Ax']
            max_order_ax = rotat_array_ax[-1, 0]
            amp1st_ax = rotat_array_ax[0, 3]

            if 'RH' in positions:
                rotat_array_r = rotat_matrix['RH']
            else:
                rotat_array_r = rotat_matrix['RV']

            amp1st_r = rotat_array_r[0, 3]
            a_r_ratio = amp1st_ax / amp1st_r

            if max_order_ax >= 3 and a_r_ratio >= 0.5:
                defect = defect_type
                level = self.__coupling_angular_misalignment_level(max_order_ax, a_r_ratio)
        else:
            pass

        return {defect: level}

    def __coupling_angular_misalignment_level(self, max_order_ax: float, a_r_ratio: float):
        """
        :param max_order_ax: maximum order of the rotation harmonics on the axial
        :param a_r_ratio: amp ratio of the 1x rotational frequency between the axial and the radial direction.
        :return:
        """
        return "Unknown"

    def __coupling_combined_misalignment(self, rotat_matrix: dict):
        defect_type = "CP3"  # 'combined_misalignment'

        defect = None
        level = None

        positions = rotat_matrix.keys()
        if 'Ax' in positions and len(positions) > 1:
            rotat_array_ax = rotat_matrix['Ax']
            ax_max_oder = rotat_array_ax[-1, 0]

            r_max_order = 0
            for pos in positions:
                if pos != 'Ax':
                    temp = rotat_matrix[pos][-1, 0]
                    if temp > r_max_order:
                        r_max_order = temp

            if ax_max_oder >= self.combined_misalignment_th and r_max_order >= self.combined_misalignment_th:
                defect = defect_type
                level = self.__coupling_combined_misalignment_level(ax_max_oder, r_max_order)

        return {defect: level}

    def __coupling_combined_misalignment_level(self, ax_max_order, r_max_order):
        return 'Unknown'

    # ----- bent shaft ----- #
    def __bent_shaft(self, rotat_matrix: dict) -> dict:
        defect_type = "CP4"  # 'bent_shaft'

        defect = None
        level = None

        if 'Ax' in rotat_matrix.keys():
            rotat_array = rotat_matrix['Ax']
            orders = rotat_array[:, 0]
            order2_idx = np.argwhere(orders == 2).flatten()
            if len(order2_idx) == 1:
                amp1 = rotat_array[0, 3]
                amp2 = rotat_array[order2_idx[0]][3]
                if np.max(orders) >= 3 and amp1 / amp2 >= self.bent_shaft_th:
                    defect = defect_type
                    level = self.__bent_shaft_level(rotat_array)

        return {defect: level}

    def __bent_shaft_level(self, rotat_matrix: np.ndarray) -> str:
        return "Unknown"

    # ----- crack ----- #
    # def __crack(self, rotat_matrix: np.ndarray) -> dict:
    #     """
    #     Not good.
    #     Require comparison between different rotational frequencies.
    #     :param rotat_matrix:
    #     :return:
    #     """
    #     defect_type = 'bent_shaft'
    #
    #     defect = None
    #     level = None
    #
    #     order = rotat_matrix[:, 0]
    #     order2_idx = np.argwhere(order == 2).flatten()
    #     if len(order2_idx):
    #         amp1 = rotat_matrix[0][3]
    #         amp2 = rotat_matrix[order2_idx][3]
    #         if np.max(order) >= 3 and np.abs(amp1 / amp2 - ValidatingData) <= 0.3:
    #             defect = defect_type
    #             level = self.__crack_level(rotat_matrix)
    #
    #     return {defect: level}
    #
    # def __crack_level(self, rotat_matrix: np.ndarray) -> str:
    #     return "Unknown"

    # ---- unbalance ----- #
    def __unbalance(self, rotat_matrix: dict) -> dict:
        """
        rotational matrix at radial
        """
        defect_type = "CP5"  # "unbalance"

        defect = None
        level = None

        for pos, rotat_array in rotat_matrix.items():
            if pos != 'Ax':
                snr1 = rotat_array[0, 4]
                amp1 = rotat_array[0, 3]
                if len(rotat_array) == 1 and (snr1 >= 15):
                    defect = defect_type
                    level = self.__unbalance_level(snr1)
                elif len(rotat_array) > 1 and (snr1 >= 15):
                    if amp1 / rotat_array[1, 3] >= self.unbalance_th:
                        defect = defect_type
                        level = self.__unbalance_level(snr1)

        return {defect: level}

    def __unbalance_level(self, snr_1: float) -> str:
        return "Unknown"

    # ----- Noise Detection ---- #
    def abnormal_noise(self, data: np.ndarray):
        """
        if the data contains clips with abnormal noises.
        :param data: input data
        :return:
        """
        len_clip = int(self.clip_len * self.sr)

        if len(data) % len_clip:
            tail = len(data) % len_clip
            data = data[:-tail]
        clips = data.reshape([-1, len_clip])

        status = 0
        for clip in clips:
            ber = self.__band_energy_ratio(data)
            if ber <= self.BER_th:
                status = 1  # abnormal
            else:
                pass

        return status

    def __band_energy_ratio(self, data: np.ndarray):
        """
        get the band energy ratio of the input spectrum.
        :param spec: the inspected data in waveform
        :return: the BER
        """
        st_tools = Stat(self.sr, self.window_ENBW)

        low_band_energy = st_tools.oa(data, self.low_band[0], self.low_band[1])
        high_band_energy = st_tools.oa(data, self.high_band[0], self.high_band[1])

        ber = low_band_energy / high_band_energy

        return ber

    # ----- Gear ----- #

    def gear_defects(self, OA: float, defect_matrices: dict, data: np.ndarray) -> dict:
        """
        Collected gear defects.
        :param data: waveform
        :param defect_matrices: harmonic matrix of the corresponding data
        :param data: np.ndarray, waveform
        :return: collection of the possible gear defects.
        """
        self.shock_finder = Shock(self.sr, self.window_ENBW, self.shock_frame, self.shock_snr_th)

        defects = {}

        if len(defect_matrices.keys()) == 1 and "GMF" in defect_matrices.keys():
            GMF_array = defect_matrices["GMF"]
            overload = self.__gear_overload(GMF_array)
            defects.update(overload)
            misalign_surface = self.__gear_misalignment(GMF_array)
            defects.update(misalign_surface)
            high_friction = self.__gear_high_friction(OA, data, GMF_array)
            defects.update(high_friction)

        GNFs = ["GNF_drive", "GNF_driven"]
        for GNF in GNFs:
            if GNF in defect_matrices.keys():
                excessive_wear = self.__gear_excessive_wear(OA, defect_matrices[GNF])
                defects.update(excessive_wear)
                broken_tooth = self.__gear_broken_tooth(data, defect_matrices[GNF])
                defects.update(broken_tooth)

        if None in defects.keys():
            defects.pop(None)

        return defects


    def __gear_overload(self, GMF_array: np.ndarray):
        defect_type = "GR5"  # overload

        defect = None
        level = None

        if len(GMF_array) and GMF_array[0, 4] >= self.overload_snr_th:
            defect = defect_type
            level = self.__gear_overload_level(GMF_array)

        return {defect: level}

    def __gear_overload_level(self, GMF_array: np.ndarray):
        return "Unknown"

    def __gear_excessive_wear(self, OA, GNF_array: np.ndarray):
        defect_type = 'GR2'  # excesssive wear

        if len(GNF_array) and OA > self.excessive_wear_OA_th:
            defect = defect_type
            level = self.__gear_excessive_wear_level(GNF_array, OA)
        else:
            defect = None
            level = None

        return {defect: level}

    def __gear_excessive_wear_level(self, GNF_array:np.ndarray, OA):
        return "Unknown"

    def __gear_broken_tooth(self, data: np.ndarray, GNF_array):
        defect_type = 'GR3'

        defect = None
        level = None

        if_shock, shock_amp, shock_snr = self.shock_finder.shock_finder(data)

        if if_shock:
            defect = defect_type
            level = self.__broken_tooth_level(shock_amp, shock_snr, GNF_array)

        return {defect: level}

    def __broken_tooth_level(self, shock_amp, shock_snr, GNF_array):
        return "Unknown"

    def __gear_misalignment(self, GMF_array: np.ndarray):
        defect_type1 = 'GR6'
        defect_type2 = 'GR1'
        if len(GMF_array) >= 2:
            defect1 = defect_type1
            defect2 = defect_type2
            level = self.__gear_misalignment_level(GMF_array)
        else:
            defect1 = None
            defect2 = None
            level = None

        return {defect1: level, defect2: level}

    def __gear_misalignment_level(self, GMF_array: np.ndarray):
        return "Unknown"

    def __gear_high_friction(self, OA: float, data: np.ndarray, GMF_array: np.ndarray):
        if_shock, shock_amp, shock_snr = self.shock_finder.shock_finder(data)

        defect_type = 'GR7'
        GMF_snr = GMF_array[0, 4]
        if OA >= self.high_friction_OA_th and if_shock and GMF_snr >= self.high_friction_GMF_th:
            defect = defect_type
            level = self.__gear_high_friction_level(OA, shock_snr, GMF_snr)
        else:
            defect = None
            level = None

        return {defect: level}

    def __gear_high_friction_level(self, OA, shock_snr, GMF_snr):
        return "Unknown"












