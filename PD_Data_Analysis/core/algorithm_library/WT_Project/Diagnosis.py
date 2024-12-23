#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
import numpy as np


class Diagnosis:

    def __init__(self, surface_defect_dscrp, defect_snr_minor, defect_snr_obv, defect_snr_vital, defect_level,
                 rotational_defect_types):

        self.snr_minor = defect_snr_minor  # snr for minor surface defects.
        self.snr_obv = defect_snr_obv  # snr for obvious surface defects.
        self.snr_vital = defect_snr_vital  # snr for vital surface defects.
        self.surface_defect_dscrp = surface_defect_dscrp
        self.defect_level = defect_level
        self.rotational_defect_types = rotational_defect_types

    def surface_defect_level(self, harmonic_matrix):
        """
        Evaluate the defect level of each characteristic frequencies, if there is any.
        :param harmonic_matrix: harmonic matrix of the surface defect characteristic frequency.
        :return:
        """
        harm_snr = harmonic_matrix[:, 4]
        if np.any(harm_snr < self.snr_minor) and np.all(harm_snr < self.snr_obv):
            defect_level = self.defect_level["0"]
        elif np.any(harm_snr >= self.snr_vital):
            defect_level = self.defect_level["2"]
        else:
            defect_level = self.defect_level["ValidatingData"]

        return self.surface_defect_dscrp, defect_level

    def rotational_defect_diagnosis(self, rotate_matrix):
        """
        Diagnose the defect type and level based on the rotational harmonics.
        :param rotate_matrix: harmonic matrix of the surface defect characteristic frequency.
        :return: list, str; defect type(s), defect level.
        """
        orders = rotate_matrix[:, 0]
        amps = rotate_matrix[:, 3]
        snrs = rotate_matrix[:, 4]

        if 1 in orders and len(orders) == 1:
            if snrs[0] >= self.snr_vital:
                defect = [self.rotational_defect_types["0"], self.rotational_defect_types["2"]]
                level = self.defect_level["2"]
            else:
                defect = []
                level = None

        elif (1 in orders) and (2 in orders) and (3 in orders):
            idx_1 = np.argwhere(orders == 1).flatten()[0]
            idx_2 = np.argwhere(orders == 2).flatten()[0]
            idx_3 = np.argwhere(orders == 3).flatten()[0]
            if all([snrs[idx_1], snrs[idx_2], snrs[idx_3]]) > self.snr_obv:
                if amps[idx_1] < amps[idx_2]:
                    defect = [self.rotational_defect_types["ValidatingData"], self.rotational_defect_types["3"]]
                    level = self.defect_level["ValidatingData"]
                else:
                    defect = [self.rotational_defect_types["2"]]
                    level = self.defect_level["ValidatingData"]
            else:
                defect = [self.rotational_defect_types["2"]]
                level = self.defect_level["0"]
        else:
            defect = []
            level = None

        return defect, level
