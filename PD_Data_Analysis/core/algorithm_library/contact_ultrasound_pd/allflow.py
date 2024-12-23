from matplotlib import pyplot as plt
import soundfile as sf
import numpy as np
import os
from core.algorithm_frame.signal_processing.fft_module import bandpass_filter
from core.algorithm_library.contact_ultrasound_pd.predict import UltrasoundPd

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

pd_inference = UltrasoundPd()


def pd_detect(data, sr):
    data_power_freq_len = int(sr / 50)

    plt.ion()
    # 循环获取一个工频周期的数据
    for i in range(len(data) // data_power_freq_len):
        data_power_freq = data[i * data_power_freq_len: (i + 1) * data_power_freq_len]

        # ================接口调用处====================
        result = pd_inference.pd_inference(data=data_power_freq,
                                           sr=sr,
                                           low_freq=18000,
                                           high_freq=30000)

        max_idx_list, max_value_list = pd_inference.get_prpd_fig()  # 获取PRPD图
        # ==============================================

        plt.clf()
        plt.scatter(max_idx_list, max_value_list)
        plt.ylim(0, 0.002)
        plt.xlim(0, data_power_freq_len)
        plt.xticks(
            [0, data_power_freq_len / 4, data_power_freq_len / 4 * 2, data_power_freq_len / 4 * 3, data_power_freq_len],
            ["0ms", "5ms", "10ms", "15ms", "20ms"])
        plt.title(result)
        plt.pause(0.01)

    plt.ioff()


if __name__ == "__main__":
    # wav_path = r"C:\Users\txkj\Desktop\重庆柱变检测\12月12日上午测试数据\10点47分 10kV红岩抽水柱上变200kVA\20231212105413__0040002A3532510B31323430__AU210.wav"
    data_dir = r"C:\Users\txkj\Desktop\重庆柱变检测\12月12日下午测试数据\10kV上马台开发区柱上变400kVA"
    for wav_name in os.listdir(data_dir):
        if not wav_name.endswith(".wav"):
            continue
        wav_path = os.path.join(data_dir, wav_name)
        data_org, sample_rate = sf.read(wav_path)
        data_input = data_org
        # 绘制data_input的10K-20KHZ时频图，
        fig = plt.specgram(data_input, Fs=sample_rate)

        # plt.ylim(5000, 30000)
        plt.show()

        exit()
        # plt.plot(data_input)
        # plt.show()
        # exit()

        # fft_data = np.fft.rfft(data_input[:sample_rate])
        # plt.plot(np.abs(fft_data[ValidatingData:]))
        # plt.show()
        # plt.close()
        pd_detect(data_input, sample_rate)
