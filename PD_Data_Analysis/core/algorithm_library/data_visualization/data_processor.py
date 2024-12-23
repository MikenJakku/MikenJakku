import numpy as np
import math
import pywt


class DataProcessor:
    @staticmethod
    def db(data_property: dict, analysis_config: dict, data: np.ndarray, sample_rate: int):
        # 分帧
        frame_size = math.floor(sample_rate / analysis_config['frameRate'])
        data = data[:len(data) // frame_size * frame_size].reshape(-1, frame_size)
        # 求有效值
        effective_data = 2 * np.mean(data ** 2, axis=-1)
        # 求db
        if data_property['correctionValue']['isDecibel']:
            db_data = 10 * np.log10(effective_data) + 94 - data_property['correctionValue']['value']
        else:
            db_data = 10 * np.log10(effective_data) + 94 - 20 * np.log10(data_property['correctionValue']['value'])
        # 返回结果
        return db_data.tolist()

    @staticmethod
    def spectrogram(data_property, analysis_config, data: np.ndarray, sample_rate: int):
        # 分帧
        frame_size = math.floor(sample_rate / analysis_config['frameRate'])
        audio_length = frame_size
        data = data[:len(data) // frame_size * frame_size].reshape(-1, frame_size)
        if analysis_config['frequencyResolution'] > 1:
            audio_length = int(data.shape[1] // analysis_config['frequencyResolution'])
            data = data[:, :audio_length]
        # 求频谱
        freq_data = 2 * np.abs(np.fft.rfft(data, axis=-1)) / audio_length
        # 频响切片
        if analysis_config['startFrequency'] > 0 and analysis_config['endFrequency'] > 0:
            freq_list = np.fft.rfftfreq(audio_length, 1.0 / sample_rate)
            freq_mask = (freq_list >= analysis_config['startFrequency']) & (freq_list < analysis_config['endFrequency'])
        elif data_property['minFrequencyResponse'] > 0 and data_property['maxFrequencyResponse'] > 0:
            freq_list = np.fft.rfftfreq(audio_length, 1.0 / sample_rate)
            freq_mask = (freq_list >= data_property['minFrequencyResponse']) & (
                    freq_list < data_property['maxFrequencyResponse'])
        else:
            freq_list = np.fft.rfftfreq(audio_length, 1.0 / sample_rate)
            freq_mask = None
            analysis_config['startFrequency'] = 0
            analysis_config['endFrequency'] = int(freq_list[-1])
        if freq_mask is not None:
            freq_data = np.apply_along_axis(
                func1d=lambda vec: vec[freq_mask],
                axis=-1,
                arr=freq_data,
            )
            analysis_config['startFrequency'] = freq_list[freq_mask][0]
            analysis_config['endFrequency'] = freq_list[freq_mask][-1]
        np.clip(freq_data, 1e-30, None, out=freq_data)
        # 转为db
        if data_property['correctionValue']['isDecibel']:
            freq_data = 20 * np.log10(freq_data) + 94 - data_property['correctionValue']['value']
        else:
            freq_data = 20 * np.log10(freq_data) + 94 - 20 * np.log10(data_property['correctionValue']['value'])
        freq_data[freq_data < 0] = 0
        # 返回结果
        return freq_data.tolist()

    @staticmethod
    def prps(data_property, analysis_config, data: np.ndarray, sample_rate: int):
        # 分帧 
        frame_rate = analysis_config['frameRate']
        db1 = pywt.Wavelet("db1")
        coif1 = pywt.Wavelet("coif1")
        power_frequency = 50
        signal_length = math.floor(sample_rate / power_frequency)
        one_second_length = power_frequency * signal_length
        # 截取最大整数个工频周期的数据长度，signal_length为一个工频周期的采样点个数
        data = data[:len(data) // one_second_length * one_second_length].reshape(-1, power_frequency, signal_length)
        data = data[:, :int(frame_rate), :].reshape(-1, signal_length)
        # 求prpd
        tmp_a, tmp_d = pywt.dwt(data, db1, mode="symmetric", axis=-1)
        data = pywt.idwt(None, tmp_d, db1, mode="symmetric", axis=-1)
        tmp_a, tmp_d = pywt.dwt(data, coif1, mode="symmetric", axis=-1)
        data = pywt.idwt(tmp_a, None, coif1, mode="symmetric", axis=-1)
        np.abs(data, out=data)
        return data.tolist()

    @staticmethod
    def prpd(data_property, analysis_config, data: np.ndarray, sample_rate: int):
        # 初始参数
        frame_rate = 50
        db1 = pywt.Wavelet("db1")
        coif1 = pywt.Wavelet("coif1")
        # 分帧
        frame_size = math.floor(sample_rate / frame_rate)
        data = data[:len(data) // frame_size * frame_size].reshape(-1, frame_size)
        num_frame = len(data)
        frame_step = int(frame_rate // analysis_config['frameRate'])
        data = data[np.arange(0, num_frame, frame_step), :]
        # 求Prpd
        tmp_a, tmp_d = pywt.dwt(data, db1, mode="symmetric", axis=-1)
        data = pywt.idwt(None, tmp_d, db1, mode="symmetric", axis=-1)
        tmp_a, tmp_d = pywt.dwt(data, coif1, mode="symmetric", axis=-1)
        data = pywt.idwt(tmp_a, None, coif1, mode="symmetric", axis=-1)
        np.abs(data, out=data)
        data /= np.max(data, axis=-1).reshape(-1, 1)
        # 3. 返回结果
        first_peak_idx = frame_size // 4
        prpd_data = []
        for _prpd_data in data:
            max_index = _prpd_data.argmax()
            new_idx = (np.arange(frame_size) - (first_peak_idx - max_index)) % frame_size
            value = _prpd_data[new_idx].tolist()
            prpd_data.append(value)
        return prpd_data

    @staticmethod
    def multi_frequency(data_property, analysis_config, data: np.ndarray, sample_rate: int):
        # 计算dft需要的权重
        frame_size = math.floor(sample_rate / analysis_config['frameRate'])
        times = np.arange(frame_size) / sample_rate
        multi_frequency = np.arange(analysis_config['startFrequency'], analysis_config['endFrequency'] + 1,
                                    analysis_config['startFrequency'])
        theta = multi_frequency * times.reshape(-1, 1)
        weight = (np.cos(theta) - 1j * np.sin(theta)).astype(np.complex64)
        # 分帧
        data = data[:len(data) // frame_size * frame_size].reshape(-1, frame_size)
        # 求倍频
        multi_frequency_data = np.abs(np.matmul(data, weight) / frame_size)
        multi_frequency_data /= (multi_frequency_data[:, 0]).reshape(-1, 1)
        # 返回结果
        return multi_frequency_data.tolist()

    @staticmethod
    def significance(data_property, analysis_config, data: np.ndarray, sample_rate: int):
        frame_rate = 50
        db1 = pywt.Wavelet("db1")
        coif1 = pywt.Wavelet("coif1")
        # 分帧
        frame_size = math.floor(sample_rate / frame_rate)  # 1920 (141,1920) (-ValidatingData, 50, 1920)
        first_peak_idx = frame_size // 4
        audio_length = frame_rate * frame_size
        # shape = (seconds * 50, sample_rate / 50)
        data = data[:len(data) // audio_length * audio_length].reshape(-1, frame_size)
        data = calc_prpd_feature(data, db1, coif1)
        return [calc_significance(data_alignment(prpd_data, first_peak_idx, frame_size)) for prpd_data in data]


def calc_prpd_feature(data: np.ndarray, db1, coif1) -> np.ndarray:
    """
    @brief 计算局放特征
    @param[in, out] data 原始数据 
    @return 局放特征
    @note batch可以不为1
    """
    tmp_a, tmp_d = pywt.dwt(data, db1, mode="symmetric", axis=-1)
    data = pywt.idwt(None, tmp_d, db1, mode="symmetric", axis=-1)
    tmp_a, tmp_d = pywt.dwt(data, coif1, mode="symmetric", axis=-1)
    data = pywt.idwt(tmp_a, None, coif1, mode="symmetric", axis=-1)
    np.abs(data, out=data)
    return data


def data_alignment(data: np.ndarray, first_peak_idx, frame_size) -> np.ndarray:
    """
    @brief 数据对齐并归一化
    @param[in] data 原始数据 
    @param[in] first_peak_idx 峰值所在的位置
    @param[in] frame_size 数据长度
    @return 对齐后的数据
    @note batch必须为1
    """
    max_index = data.argmax()
    new_idx = (np.arange(frame_size) - (first_peak_idx - max_index)) % frame_size
    data = data / data.max()
    return data[new_idx]


def calc_significance(data: np.ndarray) -> float:
    """
    @brief 计算显著性因子
    @param[in] data 输入, 一次局放特征
    @return 局放数据的显著性因子
    """
    return data.max() / data.mean()
