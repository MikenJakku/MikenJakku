#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====

from util.send_to_c import Sender

calcator = Calcator()

while True:
    data = sql.get_data()

    alarm_type, alarm_desc, alarm_data = calcator(data)

    try:
        Sender().send(alarm_type, alarm_desc, alarm_data)
    except Exception as error:
        print(error)

