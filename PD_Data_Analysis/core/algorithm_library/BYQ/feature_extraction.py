import numpy as np

from .config import transformer_config, feature_parameter


class FeatureExtraction(object):
    """特征提取类"""

    def __init__(self, sr):
        """初始化参数"""
        frame_time = feature_parameter.frame_time  # 每帧的时间长度
        self.max_freq = feature_parameter.max_freq  # 本体振动的最大频率
        self.power_freq = feature_parameter.power_freq  # 工频
        self.frame_length = int(frame_time * sr)  # 每帧的点数
        self.interval_freq = feature_parameter.interval_freq  # 计算频点值的取值范围
        self.fmin = feature_parameter.fmin_freq  # 计算低频段的能量范围【fmin:fmax】
        self.fmax = feature_parameter.fmax_freq
        self.df = 1 / frame_time  # 频率域间隔
        self.cumsum_flag = False  # 频率值计算选项，默认False
        self.feature_list = transformer_config.feature_list

    def forward(self, data: np.ndarray) -> dict:
        """
        执行函数，计算数据的特征，返回所有算法支持计算的特征
        :param data:输入数据
        :return: 字典形式特征是key，特征值是value
        """
        feature_dict = {}
        for feature in self.feature_list:  # 计算算法支持的所有特征
            try:
                feature_dict[feature] = getattr(self, '_' + feature + '_calculate')(data)  # 调用特征名对应的函数
            except AttributeError:
                raise NameError(f"特征{feature}没有对应的计算函数")
        return feature_dict

    @staticmethod
    def _peak_peak_value_calculate(data) -> np.ndarray:
        """
        计算数据的峰峰值
        :param data: 输入数据
        :return: 峰峰值
        """
        return np.max(data) - np.min(data)

    def _odd_even_ratio_calculate(self, data) -> np.ndarray:
        """
        计算奇偶次谐波比，用于直流偏磁判断
        :param data: 输入数据
        :return: 奇偶次谐波比
        """
        data_f = self._data_freq(data)  # 计算工频倍频值
        data_f = data_f ** 2  # 计算工频倍频的能量值
        odd_value = np.sum(data_f[:, 2::2], axis=1)  # 计算工频的奇次倍频的能量值
        even_value = np.sum(data_f[:, 1::2], axis=1)  # 计算工频的偶次倍频的能量值
        odd_even_ratio = odd_value / even_value
        return np.mean(odd_even_ratio)

    def _base_freq_ratio_calculate(self, data) -> np.ndarray:
        """
        计算基频（=2*工频）能量占比
        :param data: 输入数据
        :return: 基频能量占比
        """
        data_f = self._data_freq(data)  # 计算工频倍频值
        data_f = data_f ** 2  # 计算工频倍频的能量值
        all_value = np.sum(data_f[:, 1:], axis=1)  # 计算频段内倍频总能量【2*power_freq:max_freq+ValidatingData:power_freq】
        base_freq_ratio = data_f[:, 1] / all_value
        return np.mean(base_freq_ratio)

    def _main_freq_ratio_calculate(self, data) -> np.ndarray:
        """
        计算主频能量占比
        :param data: 输入数据
        :return: 主频能量占比
        """
        data_f = self._data_freq(data)  # 计算工频倍频值
        data_f = data_f ** 2  # 计算工频倍频的能量值
        all_value = np.sum(data_f[:, 1:], axis=1)  # 计算频段内倍频总能量【2*power_freq:max_freq+ValidatingData:power_freq】
        main_freq_ratio = np.max(data_f[:, 1:], axis=1) / all_value
        return np.mean(main_freq_ratio)

    def _vibration_entropy_calculate(self, data) -> np.ndarray:
        """
        计算振动熵
        :param data: 输入数据
        :return: 振动熵
        """
        data_f = self._data_freq(data)  # 计算工频倍频值
        data_f = data_f ** 2  # 计算工频倍频的能量值
        data_f = data_f[:, 1::1]  # 取【2*power_freq:max_freq+ValidatingData:power_freq】计算振动熵
        data_f = data_f / np.sum(data_f, axis=1, keepdims=True)  # 计算工频倍频的能量占比
        vibration_entropy = -np.sum(data_f * np.log2(data_f), axis=1)  # 计算振动熵
        return np.mean(vibration_entropy)

    @staticmethod
    def _rms_value_calculate(data) -> np.ndarray:
        """
        计算有效值rms
        :param data: 输入数据
        :return: 有效值rms
        """
        return np.sqrt(np.mean(data ** 2))

    def _normal_vibra_ratio_calculate(self, data) -> np.ndarray:
        """
        计算工频倍频能量占总能量(频段范围【fmin_freq:fmax_freq】)比，判断此数据是否可用于变压器评价
        :param data:输入数据
        :return:工频倍频能量占总能量比
        """
        data = data[:data.size // self.frame_length * self.frame_length].reshape(-1,
                                                                                 self.frame_length)  # frame_length进行分帧
        data_f_all = np.abs(np.fft.fft(data, axis=1)[:, :self.frame_length // 2])  # 计算振幅谱
        data_f = self._data_freq(data)
        normal_vibra_ratio = np.sum(data_f ** 2) / np.sum(
            data_f_all[:, int(self.fmin / self.df):int(self.fmax / self.df)+1] ** 2)
        return normal_vibra_ratio

    def _data_freq(self, data) -> np.ndarray:
        """
        计算工频倍频值
        :param data:
        :return: 工频倍频值
        """
        data = data[:data.size // self.frame_length * self.frame_length].reshape(-1,
                                                                                 self.frame_length)  # frame_length进行分帧
        data_f_all = np.abs(np.fft.fft(data, axis=1)[:, :self.frame_length // 2])  # 计算振幅谱
        data_f_all[:, 0] = 0  # 直流分量置零
        # 计算给定频段内【power_freq:max_freq+ValidatingData:power_freq】倍频点个数
        freq_num = (self.max_freq - self.power_freq) // self.power_freq + 1
        data_f = np.zeros((data_f_all.shape[0], freq_num))  # 工频倍频值数据
        # 频率值计算选项，False是【-interval_freq，interval_freq】范围的最大值，True是【-interval_freq，interval_freq】范围的累加值，受噪声影响较大
        if self.cumsum_flag:
            for ii in np.arange(freq_num):
                data_f[:, ii] = np.sum(data_f_all[:,
                                       int(((ii + 1) * self.power_freq - self.interval_freq) / self.df):
                                       int(((ii + 1) * self.power_freq + self.interval_freq) / self.df)], axis=1)
        else:
            for ii in np.arange(freq_num):
                data_f[:, ii] = np.max(data_f_all[:, 
                                       int(((ii + 1) * self.power_freq - self.interval_freq) / self.df):
                                       int(((ii + 1) * self.power_freq + self.interval_freq) / self.df)], axis=1)
        return data_f
