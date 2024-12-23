#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
import psutil
import time

memory = psutil.virtual_memory()

print("总内存：", memory.total/1024/1024/1024)
time.sleep(1)
print("已使用内存：", memory.used/1024/1024/1024)
print("可用内存：", memory.available/1024/1024/1024)

cpu_percent = psutil.cpu_percent()
print("CPU占用率：", cpu_percent)
