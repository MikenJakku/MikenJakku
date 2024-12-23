#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
import numpy as np


def rms(data):
    """
    Root-mean-square value of the blocks
    :param data: 1D or 2D array
    :return: 1D array; rms value
    """
    if len(data.shape) == 1:
        vrms = np.sqrt(np.average(data ** 2))
        vrms = np.array([vrms])
    else:
        vrms = np.sqrt(np.average(data ** 2, axis=1))

    return vrms
