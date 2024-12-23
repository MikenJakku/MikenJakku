#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
import os
import shutil
from tqdm import tqdm

data_dir = r"F:"
target_dir = r"\\192.168.3.80\算法\声纹-算法\叶片数据\正常叶片2"

for file_name in tqdm(os.listdir(data_dir)):
    if not file_name.endswith(".wav"):
        continue
    channel_name = file_name.split("-")[0]
    target_path = os.path.join(target_dir, channel_name)
    if not os.path.exists(target_path):
        os.mkdir(target_path)
    shutil.copy(os.path.join(data_dir, file_name), target_path)
