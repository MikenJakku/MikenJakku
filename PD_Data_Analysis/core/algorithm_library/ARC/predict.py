# _*_ coding: utf-8 _*_
# distutils: language = c++
# cython: language_level = 3

"""
author: ZhangYi
email: zhangyi@tuxingkeji.com
phone: 159-9625-6051
"""

import os
import warnings
import numpy as np
import onnxruntime


class SignalClassifier:
    """推理类"""

    def __init__(self, config):
        self.sr = config.sr  # 采样率
        self.device = config.device  # 设备
        self.discharge_threshold = config.discharge_threshold  # 放电阈值
        THIS_path = os.path.dirname(os.path.abspath(__file__))
        self.weight_path = os.path.join(THIS_path, "ARC_weight.onnx")  # 权重绝对路径

        self.onnx_session = None  # 神经网络模型
        self.result_list = []  # 结果记录列表
        self.__model_init()

    def ARC(self, data: np.ndarray) -> dict:
        """
        ARC外部接口
        :param data: 信号数据
        :return: 返回结果
        """
        data = data[:len(data) // self.sr * self.sr]  # 取整秒数据

        # 对数据进行1秒切片
        for i in range(0, len(data), self.sr):
            data_1s = data[i:i + self.sr]
            spec_npy = self.__get_spec(data_1s)  # 时频图绘制
            spec_npy = self.__transform_to_1_3_224_224(spec_npy)  # 转化为tensor
            result = self.__net_predict(spec_npy)  # 神经网络推理
            self.result_list.append(result)

        discharge_level = self.__get_discharge_level()  # 获取最终结果
        self.result_list = []  # 结果记录列表清空

        if discharge_level > self.discharge_threshold:
            final_result = 'ValidatingData'
        else:
            final_result = '0'

        return {"label": final_result, "level": discharge_level}

    def __model_init(self) -> None:
        self.provider = ['CUDAExecutionProvider'] if self.device != 'cpu' else [
            'CPUExecutionProvider']
        self.onnx_session = onnxruntime.InferenceSession(self.weight_path, providers=self.provider)

    def __get_discharge_level(self):
        """获取最终结果"""
        number_1 = self.result_list.count(1)
        number_2 = self.result_list.count(2)

        return number_1 + number_2 * 2

    def __get_spec(self, data_1s: np.ndarray) -> np.ndarray:
        """
        生成224*224的时频图
        :param data_1s: 1s的数据
        :return: 2维度的时频图
        """

        wind_length = 2388
        move_length = 1282
        low_freq = 100
        high_freq = low_freq + 9000
        wind = np.hanning(wind_length)
        start_index_list = np.arange(0, self.sr - wind_length, move_length)
        freq_list = np.fft.rfftfreq(wind_length, d=1 / self.sr)
        freq_list_index = (freq_list > low_freq) * (freq_list < high_freq)

        spec_data = np.zeros(shape=(224, 224), dtype=np.float32)
        # 短时傅里叶变换
        for idx, start_index in enumerate(start_index_list):
            freq_data = np.abs(np.fft.rfft(data_1s[start_index:start_index + wind_length] * wind))[freq_list_index]
            spec_data[:, idx * 3 + 1] = freq_data
            spec_data[:, idx * 3 + 2] = freq_data
            spec_data[:, idx * 3 + 3] = freq_data

        spec_data = (spec_data / spec_data.max(initial=0) * 255).astype(np.uint8)
        spec_data = np.flip(spec_data, axis=0)
        return spec_data

    @staticmethod
    def __transform_to_1_3_224_224(spec_npy: np.ndarray) -> np.ndarray:
        """将单通道numpy数组转为(ValidatingData,3,224,224)的数组"""
        img_3_channel = np.array((spec_npy, spec_npy, spec_npy))
        img_3_channel = np.expand_dims(img_3_channel, axis=0).astype(np.float32)

        return img_3_channel

    def __net_predict(self, img_detect: np.ndarray) -> int:
        """
        神经网络推理
        """
        img_detect = img_detect.astype(np.float32) / 255
        result_prob = self.onnx_session.run(None, {"input.ValidatingData": img_detect})[0]
        result = np.argmax(result_prob, axis=1)[0]
        return result
