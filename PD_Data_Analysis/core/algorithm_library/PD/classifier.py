"""
传入一个prpd，返回一个放电类型
"""

import numpy as np
# from .parameter import ReadConfig


def get_PD_type(prpd: np.ndarray, config) -> int:
    """
    根据归一化后的prpd，对放电类型进行分类
    """
    assert len(prpd) % 4 == 0, "prpd的长度必须可以被4整除"

    first_peak = prpd[:config.signal_length // 2]  # 前半个周期
    second_peak = prpd[config.signal_length // 2:]  # 后半个周期
    first_peak_type = get_peak_type(first_peak, config)
    second_peak_type = get_peak_type(second_peak, config)

    if first_peak_type == config.no_discharge and second_peak_type == config.no_discharge:
        # 都不放电，则都不是放电
        return config.no_discharge
    elif first_peak_type == config.suspended_discharge and second_peak_type == config.suspended_discharge:
        # 都是悬浮放电，则都是悬浮放电
        return config.suspended_discharge
    elif first_peak_type == config.surface_discharge and second_peak_type == config.surface_discharge:
        # 都是沿面放电，则都是沿面放电
        return config.surface_discharge
    elif first_peak_type == config.double_discharge and second_peak_type == config.double_discharge:
        # 都是双峰放电，则都是双峰放电
        return config.double_discharge
    elif first_peak_type != second_peak_type:
        # 在这个逻辑下，两个峰判断结果不一致
        if second_peak_type == config.no_discharge:
            # 只有一个峰，那么就认为是电晕型放电
            return config.corona_discharge
        if first_peak_type == config.no_discharge:
            return config.no_discharge
        if first_peak_type == config.double_discharge or second_peak_type == config.double_discharge:
            if first_peak_type == config.suspended_discharge or second_peak_type == config.suspended_discharge:
                # 其中一个是悬浮放电，则为悬浮放电
                return config.suspended_discharge
            elif first_peak_type == config.surface_discharge or second_peak_type == config.surface_discharge:
                # 其中一个是沿面放电，则为沿面放电
                return config.surface_discharge
            else:
                return config.double_discharge
        elif (first_peak_type == config.surface_discharge or
              second_peak_type == config.surface_discharge) and \
                (first_peak_type == config.suspended_discharge or
                 second_peak_type == config.suspended_discharge):
            return config.double_discharge
        else:
            raise RuntimeError("放电类型逻辑未能覆盖1")

    else:
        raise RuntimeError("放电类型逻辑未能覆盖2")


def width_of_PD_percent(data: np.ndarray, PD_num: float, config) -> int:
    """
    计算一定比例下点被覆盖的峰宽
    """

    data_max_idx = len(data) - 1  # 信号的最大索引
    mid_idx = data_max_idx // 2  # 中央的索引。不管是不是奇数还是偶数

    PD_points_count = 0
    left_width = 0  # 左峰宽
    right_width = 0  # 右峰宽

    for i in range(mid_idx, -1, -1):
        if data[i] > 0:
            # 左侧点遍历，找出超过基底噪音的点的索引
            PD_points_count += 1
            left_width = mid_idx - i

        if data[data_max_idx - i] > 0:
            # 右侧点遍历，找出超过基底噪音的点的索引
            PD_points_count += 1
            right_width = mid_idx - i

        if PD_points_count / PD_num > config.PD_num_rate:
            return left_width + right_width

    raise ValueError("峰宽计算逻辑未覆盖")


def get_peak_type(half_prpd: np.ndarray, config) -> int:
    """
    判别峰的类型：悬浮 沿面 正常 无法识别
    """
    temp = config.no_discharge  # 用于记录其他噪声比下的峰类型

    for noise_rate in np.arange(config.lowest_noise_amp, config.highest_noise_amp + 1e-5, 0.1):
        # 1e-5是为了遍历到闭区间，有些浮点数的计算误差
        # 由最小噪音开始遍历各个信噪比，逐步向上扫描判断是否有峰
        PD_points = np.zeros_like(half_prpd)
        PD_num = 0
        PD_num_in_mid = 0
        for i in range(len(half_prpd)):
            # 逐点遍历，找出超过基底噪音的点的索引
            if half_prpd[i] >= noise_rate:
                PD_points[i] = half_prpd[i]
                PD_num += 1
                if config.peak_left <= i <= config.peak_right:
                    PD_num_in_mid += 1
        if PD_num_in_mid <= 3:
            return temp  # 点太少则直接返回一个无放电
        peak_width = width_of_PD_percent(PD_points, PD_num=PD_num, config=config)

        if peak_width <= config.narrow_width:
            # 窄峰则为悬浮放电
            return config.suspended_discharge
        elif peak_width >= config.wide_width:
            # 峰太宽则为不放电
            if noise_rate >= config.highest_noise_amp:
                # 若曾经判断为某种放电，那么就认为是那种放电
                # 若从未判断出过放电，那么就返回no_discharge
                return temp
            else:
                continue
        elif config.surface_width <= peak_width <= config.wide_width:
            # 峰宽的为沿面放电
            if noise_rate >= 0.4:
                return config.surface_discharge
            else:
                temp = config.surface_discharge
                continue
        elif config.narrow_width <= peak_width <= config.surface_width:
            # 若不好说，则为无法判断的双峰放电
            return config.double_discharge
    raise RuntimeError("没有找到峰的类型")
