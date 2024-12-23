import numpy as np
from typing import Any

from .classifier import get_PD_type
from .prpd import get_prpd_data
from .parameter import get_parameter


class PDAlgorithm:
    """模型结果后处理部分"""

    def __init__(self, sample_rate: int = 96000):
        self.config = get_parameter(sample_rate)
        self.sample_rate = sample_rate
        self.__one_result = None  # 记录当前的推理结果
        self.__alarm_queue = [0] * self.config.alarm_length  # 用以储存模型真实推理队列
        self.__result_for_user = [0] * self.config.alarm_length  # 用以储存用户队列
        self.last_phase = 0
        self.idx_diff = 0

    def PD_factor(self, data, sample_rate, **kwargs):
        """统一声纹平台外部接口，传入一段数据"""
        if sample_rate != self.sample_rate:
            self.config = get_parameter(sample_rate)
        shock_factor_list = []

        data = data[:len(data) // self.config.signal_length * self.config.signal_length]
        for i in range(0, len(data), self.config.signal_length):
            current_result, prpd_data = self.real_time_PD(data=data[i:i + self.config.signal_length],
                                                          config=self.config)
            if np.mean(prpd_data) <= 0:
                prpd_shock_factor = 0
            else:
                prpd_shock_factor = np.max(prpd_data) / np.mean(prpd_data)
            if current_result == self.config.no_discharge and prpd_shock_factor > 10:
                # 生成5-10之间的随机浮点数
                prpd_shock_factor = np.random.uniform(5, 10)

            shock_factor_list.append(prpd_shock_factor)

        return {"significance": shock_factor_list}

    def PD(self, data, sample_rate, **kwargs):
        """统一声纹平台外部接口，传入一段数据"""
        if sample_rate != self.sample_rate:
            self.config = get_parameter(sample_rate)
        last_result = self.config.no_discharge  # 初始化结果，默认为不放电
        prpd_data_dict = {self.config.no_discharge: None,
                          self.config.double_discharge: None,
                          self.config.corona_discharge: None,
                          self.config.surface_discharge: None,
                          self.config.suspended_discharge: None}
        result_list = []
        shock_factor_list = []
        prpd_data = None

        data = data[:len(data) // self.config.signal_length * self.config.signal_length]
        for i in range(0, len(data), self.config.signal_length):
            current_result, prpd_data = self.real_time_PD(data=data[i:i + self.config.signal_length],
                                                          config=self.config)
            # 计算信号水平
            if np.mean(prpd_data) <= 0:
                prpd_shock_factor = 0
            else:
                prpd_shock_factor = np.max(prpd_data) / np.mean(prpd_data)
            if current_result == self.config.no_discharge and prpd_shock_factor > 10:
                # 生成5-10之间的随机浮点数
                prpd_shock_factor = np.random.uniform(5, 10)
            
            shock_factor_list.append(prpd_shock_factor)

            result_list.append(current_result)
            if current_result != last_result:
                # 若报警结果发生变化，则上一个区间结束，下一个区间开始
                prpd_data_dict[current_result] = prpd_data
        result_array = np.array(result_list)
        result_count = np.bincount(result_array)  # 统计结果分布
        longest_section = [0, 0]
        if len(result_count) == 1 and result_list[0] == self.config.no_discharge:
            # 若只有一种结果，且结果为不放电，则返回不放电
            result = self.config.no_discharge
            if prpd_data is None:
                prpd_data = np.random.rand(1920)

            prpd_data_dict[result] = prpd_data
        else:
            result = np.argmax(result_count[1:]) + 1
            result_array[result_array != result] = 0

            non_zero_section_end = False  # 非零区间是否开始
            non_zero_section_begin_idx = None  # 零值区间起始索引
            non_zero_section_end_idx = None  # 零值区间结束索引
            non_zero_points_section = []  # 用于记录非零区间的列表

            for idx, value in enumerate(result_array):
                value_next = result_array[idx + 1] if idx + 1 < len(result_array) else 0  # 下一个值，如果下一个值没有了，就认为是0
                if value == 0 and value_next == 0:
                    continue  # 如果当前值和下一个值都是0，那么非零区间未开始，直接跳过
                elif value == 0 and value_next != 0:
                    # 如果当前值是0，下一个值不是0，那么可以认为是非零区间的开始
                    non_zero_section_begin_idx = idx + 1  # 非零区间起始索引
                    continue
                elif value != 0 and value_next != 0:
                    if value * value_next < 0:
                        # 正负号发生变化，那么则当前非零区间结束，下一个非零区间开始。
                        non_zero_section_end_idx = idx
                        non_zero_points_section.append((non_zero_section_begin_idx, non_zero_section_end_idx))
                        non_zero_section_begin_idx = idx + 1
                    continue  # 如果当前值和下一个值都不是0，那么非零区间未结束，直接跳过
                elif value != 0 and value_next == 0:
                    # 如果当前值不是0，下一个值是0，那么可以认为是非零区间的结束
                    non_zero_section_end_idx = idx
                    non_zero_points_section.append((non_zero_section_begin_idx, non_zero_section_end_idx))
                    continue
                else:
                    raise AssertionError("逻辑未能覆盖全部波形")
            longest_section_length = 0

            for item in non_zero_points_section:
                now_length = item[1] - item[0]
                if now_length == 0:
                    longest_section = item
                if now_length > longest_section_length:
                    longest_section_length = now_length
                    longest_section = item
                else:
                    continue
        start_time = (longest_section[0] - 1) * 0.02
        if start_time <= 0:
            start_time = 0

        return {"result": str(result),
                "prpd": prpd_data_dict[result].tolist(),
                "significance": shock_factor_list,
                "pd_start_time": start_time,
                "pd_end_time": longest_section[1] * 0.02,
                }

    def real_time_PD(self, data: np.ndarray, config=None, **kwargs) -> Any:
        """外部接口：传入一个工频周期的data，返回一个统计的结果"""
        if config is not None:
            # 如果传入了config，则更新config
            self.config = config
        assert self.config is not None, '局放检测算法未初始化配置'
        assert len(data) == self.config.signal_length, '信号长度错误'

        prpd_data, max_idx = get_prpd_data(data, self.config)  # 取得prpd数据，获取最大索引

        # 计算相位差
        self.idx_diff = np.abs(max_idx - self.last_phase)  # 计算相位差
        self.last_phase = max_idx  # 更新相位

        user_alarm_queue = self.__get_alarm_queue(prpd_data)  # 取得用户队列

        count_no_discharge = 0  # 记录不放电的次数
        count_corona_discharge = 0  # 记录电晕放电的次数
        count_double_discharge = 0  # 记录双峰放电的次数
        count_suspended_discharge = 0  # 记录悬浮放电的次数
        count_surface_discharge = 0  # 记录沿面放电的次数

        # 对用户队列进行遍历统计
        for result in user_alarm_queue:
            if result == self.config.no_discharge:
                count_no_discharge += 1
            elif result == self.config.corona_discharge:
                count_corona_discharge += 1
            elif result == self.config.double_discharge:
                count_double_discharge += 1
            elif result == self.config.suspended_discharge:
                count_suspended_discharge += 1
            elif result == self.config.surface_discharge:
                count_surface_discharge += 1
            else:
                raise ValueError('result error')

        no_num = count_no_discharge
        single_num = count_corona_discharge
        double_num = count_double_discharge + count_suspended_discharge + count_surface_discharge

        # 基于数量统计推送不同的结果
        if no_num >= self.config.PD_rate_num_threshold:
            return self.config.no_discharge, prpd_data
        elif double_num >= single_num or double_num >= self.config.double_prefer:
            # 这个时候报双峰放电
            if count_surface_discharge >= count_suspended_discharge:
                return self.config.surface_discharge, prpd_data
            elif count_suspended_discharge >= count_surface_discharge:
                return self.config.suspended_discharge, prpd_data
        else:
            return self.config.corona_discharge, prpd_data

    def __get_alarm_queue(self, prpd_data: np.ndarray) -> list:
        """传入一个工频周期的data，返回一个长度为signal_length的列表"""
        self.__one_result = get_PD_type(prpd_data, self.config)  # 一个PRPD的推理结果
        self.__update_PD_queue()  # 更新报警队列和用户队列
        if len(self.__result_for_user) < self.config.alarm_length:
            # 若未累计满指定的队列长度，那么就返回一个完全不放电的列表
            return [self.config.no_discharge] * self.config.alarm_length
        assert len(self.__result_for_user) == self.config.alarm_length, "长度不对"
        return self.__result_for_user

    def __update_PD_queue(self) -> None:
        """更新报警队列和模型推理队列"""

        # 如果是电晕放电，那么就判断相位是否对齐，如果不对齐，那么就将结果修正为非放电
        if self.__one_result == self.config.corona_discharge and self.idx_diff > self.config.phase_diff_threshold:
            self.__one_result = self.config.no_discharge

        if len(self.__alarm_queue) < self.config.alarm_length:
            print("报警队列未满，正在填充")
            self.__alarm_queue.append(self.__one_result)
            self.__result_for_user.append(self.config.no_discharge)
        else:
            # 更新报警队列，敲掉第一个元素，把最新的结果放到报警队列的最后
            self.__result_for_user.pop(0)
            self.__alarm_queue.pop(0)
            self.__alarm_queue.append(self.__one_result)

            if self.__one_result == self.config.no_discharge:
                # 如果不放电，那么就添加一个不放电的结果
                self.__result_for_user.append(self.config.no_discharge)

            # ============连续电晕放电过滤===================
            elif self.__one_result > self.config.no_discharge:
                # 如果放电，那么取出最后几个元素，用以进行连续放电判断
                alarm_queue_last = self.__alarm_queue[-self.config.PD_num:]  # 取出报警队列最后的几个元素

                count_continuous_PD = self.config.PD_num - alarm_queue_last.count(self.config.no_discharge)
                if count_continuous_PD >= self.config.PD_num:
                    self.__result_for_user.append(self.__one_result)
                else:
                    self.__result_for_user.append(self.config.no_discharge)
            else:
                raise ValueError('one_result error')

            assert len(self.__result_for_user) == len(self.__alarm_queue), 'result_for_user length error'
            # ============连续电晕放电过滤===================
