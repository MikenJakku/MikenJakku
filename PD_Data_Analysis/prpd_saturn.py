import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
import os
from core.algorithm_library.contact_ultrasound_pd.predict import UltrasoundPd
from scipy import signal

pd_inference = UltrasoundPd()
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


def prpd(data, sr, roots, file_):
    sp = int(sr/50)  # 工频50Hz
    count = 0
    for i in range(len(data)//sp):
        data_p = data[i*sp: (i+1)*sp]  # 每个工频周期的采样点
        # ===================接口调用===================
        result = pd_inference.pd_inference(data=data_p,
                                           sr=sr,
                                           low_freq=15000,
                                           high_freq=30000)
        max_index_list, max_value_list = pd_inference.get_prpd_fig()
        # ============================================
        plt.figure()
        plt.scatter(max_index_list, max_value_list)
        # plt.ylim(0, 0.02)
        plt.xlim(0, sp)
        plt.xticks(
            [0, sp / 4, sp / 4 * 2, sp / 4 * 3, sp],
            ["0ms", "5ms", "10ms", "15ms", "20ms"])

        if result not in ['检测中']:
            plt.title(result)
            plt.savefig(os.path.join(roots, file_) + str(i) + '.jpg')
            print(i)

        plt.clf()
        plt.close()


if __name__ == '__main__':
    file_path = r"D:\DOCU\Seafile\Seafile\MyDocu\NJU\Work\PD_Exp\Data\Try"
    for roots, dirs, files in os.walk(file_path):
        if len(files) > 0:
            for file_ in files:
                if os.path.splitext(file_)[1] == '.wav':
                    data, sr = sf.read(os.path.join(roots, file_))
                    # data = data[:int(sr*2)]
                    # data = data[:, 0]
                    b, a = signal.butter(8, 0.01, 'highpass')
                    wave = signal.filtfilt(b, a, data)
                    # if len(data)/sr < 4.5:
                    #     print(os.path.join(roots, file_))
                    # else:
                    #     continue
                    prpd(data, sr, roots, file_)
