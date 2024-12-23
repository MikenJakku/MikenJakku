import numpy as np


class UltrasoundPd:
    def __init__(self):
        # 枚举放电类型
        self.PD_TYPE = {
            0: "正常",
            1: "一簇",
            2: "两簇",
            404: "局放",
            -1: "检测中"
        }

        # 预设参数们
        self.mean_distance_threshold = 200  # 分类器判断阈值，与采样率相关
        self.power_freq = 50  # 工频
        self.period_num = 100  # prpd绘制的周期个数
        self.points_num = 2 * self.period_num  # 打点个数

        self.signal_len = None  # 信号长度
        self.max_peak_idx = None  # 最大峰值索引值

        self.peak_idx_array = None  # 峰值索引值数组
        self.peak_value_array = None  # 峰值数组
        self.peak_idx_prpd_array = None  # prpd图中的峰值索引值列表

    def pd_inference(self, data: np.ndarray, sr: int, low_freq: float = None, high_freq: float = None):
        """
        推理函数
        :param data: 1D. 传入20ms的数据
        :param sr: 采样率
        :param low_freq: 滤波低频
        :param high_freq: 滤波高频
        :return: 局放检测结果
        """
        self.signal_len = int(sr // self.power_freq)  # 采样率是会变化的
        self.max_peak_idx = self.signal_len // 4

        # 一个毫无意义的断言。确保传入是20ms数据即可。
        assert len(data) == self.signal_len, "传入数据长度不正确，请传入20ms的数据"

        self.__get_pd_peak(data_prpd=self.__data_filter(data=data, sr=sr, low_freq=low_freq, high_freq=high_freq))
        self.__get_current_prpd_data()
        return self.__classify()

    def __classify(self):
        """
        分类函数，原理为使用标准直线标识均匀分布，若出现局放，则会出现明显的偏离。
        """
        if len(self.peak_idx_array) < self.period_num * 2:
            # 若打点个数不足，则返回检测中
            return self.PD_TYPE[-1]
        else:
            # 若打点个数足够，则进行分类
            pd_peak = 0
            idx_sorted = np.array(sorted(self.peak_idx_prpd_array))

            # =======================前半周期分类==============================
            # 所有值小于self.signal_len // 2的点为前半周期点
            former_x_points = np.where(idx_sorted < self.signal_len // 2)
            former_y_points = idx_sorted[former_x_points]
            points_x_start = 0
            points_x_end = np.max(former_x_points)
            points_y_start = 0
            points_y_end = self.signal_len // 2
            k = (points_y_end - points_y_start) / (points_x_end - points_x_start)

            y_standard = k * np.arange(0, points_x_end-points_x_start + 1) + points_y_start
            distance_average = np.mean(np.abs(y_standard - former_y_points))
            if distance_average > self.mean_distance_threshold:
                pd_peak += 1

            # =======================后半周期分类==============================
            # 所有值小于self.signal_len // 2的点为前半周期点
            later_x_points = np.where(idx_sorted >= self.signal_len // 2)
            later_y_points = idx_sorted[later_x_points]
            points_x_start = np.min(later_x_points)
            points_x_end = self.points_num
            points_y_start = self.signal_len // 2
            points_y_end = self.signal_len
            k = (points_y_end - points_y_start) / (points_x_end - points_x_start)
            y_standard = k * np.arange(0, points_x_end-points_x_start) + points_y_start
            distance_average = np.mean(np.abs(y_standard - later_y_points))
            if distance_average > self.mean_distance_threshold:
                pd_peak += 1

            return self.PD_TYPE[pd_peak]

    @staticmethod
    def __data_filter(data, sr, low_freq=None, high_freq=None):
        """
        对数据进行傅里叶变换，取出特定频率范围，再进行傅里叶反变换
        """
        if low_freq is None and high_freq is None:
            # todo：后续在此补充自动的频段选择算法。
            low_freq = 18000
            high_freq = 35000

        # ValidatingData、对数据进行傅里叶变换
        fft_data = np.fft.rfft(data)
        # 2、计算频谱索引
        fft_index = np.fft.rfftfreq(len(data), 1 / sr)
        # 3、取出特定频率范围
        fft_data[(fft_index < low_freq) | (fft_index > high_freq)] = 0
        # 4、进行傅里叶反变换
        ifft_data = np.fft.irfft(fft_data)
        # plt.plot(np.abs(ifft_data))
        # plt.show()
        return np.abs(ifft_data)

    def get_prpd_fig(self):
        """
        外部接口：获取PRPD图
        """
        return self.peak_idx_prpd_array, self.peak_value_array

    def __get_current_prpd_data(self):
        """
        获取PRPD图，因展示需要，需要对数据进行对齐。
        将会对索引值进行操作，将最大值所在的索引值置为四分之一个工频周期处
        """
        self.peak_idx_prpd_array = self.peak_idx_array.copy()
        # 获取最大值所在的索引值
        max_idx = np.argmax(self.peak_value_array)
        # 索引平移
        self.peak_idx_prpd_array = self.peak_idx_array + self.max_peak_idx - self.peak_idx_array[max_idx]

        # 对超出范围的索引值进行处理
        self.peak_idx_prpd_array[self.peak_idx_prpd_array < 0] += self.signal_len
        self.peak_idx_prpd_array[self.peak_idx_prpd_array > self.signal_len] -= self.signal_len

    def __get_pd_peak(self, data_prpd):
        """
        取放电峰
        """
        # 前一半数据
        max_idx_former = np.argmax(data_prpd[:len(data_prpd) // 2])
        max_value_former = data_prpd[max_idx_former]

        # 后一半数据
        max_idx_latter = np.argmax(data_prpd[len(data_prpd) // 2:])
        max_value_latter = data_prpd[max_idx_latter + len(data_prpd) // 2]

        if self.peak_idx_array is None:
            self.peak_idx_array = np.array([max_idx_former, max_idx_latter + len(data_prpd) // 2])
            self.peak_value_array = np.array([max_value_former, max_value_latter])
            return

        if len(self.peak_idx_array) >= self.period_num * 2:
            # 若打点个数已满，则删除前两个
            self.peak_idx_array = self.peak_idx_array[2:]
            self.peak_value_array = self.peak_value_array[2:]

        self.peak_idx_array = np.append(self.peak_idx_array, max_idx_former)
        self.peak_value_array = np.append(self.peak_value_array, max_value_former)
        self.peak_idx_array = np.append(self.peak_idx_array, max_idx_latter + len(data_prpd) // 2)
        self.peak_value_array = np.append(self.peak_value_array, max_value_latter)
