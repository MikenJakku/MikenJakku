#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
from statsmodels.tsa.stattools import kpss


class Trending:
    def __init__(self):
        pass

    @staticmethod
    def if_trend(feature):
        pvalue = kpss(feature, regression='c', nlags='auto')[1]
        if pvalue <= 0.05:
            trending_status = True
        else:
            trending_status = False

        return trending_status
