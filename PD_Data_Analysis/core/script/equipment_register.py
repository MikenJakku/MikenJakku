#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====
from core.CRUD_toolkits.CRUD import CRUD
import json


def equipment_register():
    """
    设备注册
    """
    with open("equipment_info.json", "r", encoding="utf-8") as f:
        equipment_info = json.load(f)

    for monitor_name, equip_id_list in equipment_info.items():
        crud = CRUD(monitor_name)
        for equip_id in equip_id_list:
            crud.equipment_register(equip_id)


# equipment_register()
crud = CRUD("Thresholding.json")
crud.equipment_register("11F")
crud.equipment_register("12F")
crud.equipment_register("13F")
crud.equipment_register("14F")
