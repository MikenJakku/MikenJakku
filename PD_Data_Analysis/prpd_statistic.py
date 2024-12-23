import os
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf
from scipy.signal import butter, filtfilt
from matplotlib import rcParams


class Prpd:
    def __init__(self, data_path):
        self.wave_path = []
        for roots, dirs, files in os.walk(data_path):
            if len(files) > 0:
                for file_ in files:
                    if os.path.splitext(file_)[1] == '.wav':
                        # 数据目录读取
                        self.wave_path.append(os.path.join(roots, file_))

    def prpd_max(self, fixed_frame_num, point_num, hop_len=None):
        prpd_max_set = []
        prpd_max_idx_set = []
        prpd_max_phase_set = []
        for s in range(len(self.wave_path)):
            # 数据读取 + 预处理
            wave_path_s = self.wave_path[s]
            wave_s, sr = sf.read(wave_path_s)
            wave_s /= np.max(wave_s)
            if len(wave_s.shape) > 1:
                wave_s = wave_s[:, 0]
            b, a = butter(8, 0.01, 'highpass')
            wave_s = filtfilt(b, a, wave_s)
            # 计算PRPD
            t = 0.02
            pd_len = int(sr*t)
            frame_point_num = int(pd_len * point_num)
            if fixed_frame_num <= int(len(wave_s) // frame_point_num):
                frame_num = fixed_frame_num
            else:
                frame_num = int(len(wave_s) // frame_point_num)
            prpd_max = np.zeros((frame_num, point_num*2))
            prpd_max_idx = np.zeros((frame_num, point_num*2))
            prpd_max_phase = np.zeros((frame_num, point_num*2))
            for i in range(frame_num):
                prpd_i = wave_s[i*frame_point_num: (i+1)*frame_point_num]
                for j in range(point_num):
                    prpd_i_j = np.abs(prpd_i[j*pd_len: (j+1)*pd_len])
                    max1_idx = np.argmax(prpd_i_j[0:pd_len//2])
                    max2_idx = np.argmax(prpd_i_j[pd_len//2: pd_len-1])
                    prpd_max_idx[i, int(2*j)] = int(max1_idx)
                    prpd_max_idx[i, int(2*j)+1] = int(max2_idx + pd_len//2)
                    prpd_max_phase[i, int(2*j)] = max1_idx / pd_len*360
                    prpd_max_phase[i, int(2*j)+1] = (max2_idx + pd_len//2) / pd_len*360
                    prpd_max[i, int(2*j)] = prpd_i_j[int(max1_idx)]
                    prpd_max[i, int(2*j)+1] = prpd_i_j[int(max2_idx + pd_len//2)]
            prpd_max_set.append(prpd_max)
            prpd_max_idx_set.append(prpd_max_idx)
            prpd_max_phase_set.append(prpd_max_phase)
            print(f'音频PRPD维度：{prpd_max.shape}')
        return prpd_max_set, prpd_max_idx_set

    def prpd_plt(self, prpd_set, prpd_max_phase_set, title):
        config = {
            "font.family": 'Times New Roman',
        }
        rcParams.update(config)
        for s in range(len(self.wave_path)):
            y = prpd_set[s]
            x = prpd_max_phase_set[s]
            frame_num = y.shape[0]
            statistics_limit = np.percentile(np.sort(np.abs(y)), 99)
            for i in range(frame_num):
                print(f'第{s}段音频第{i}张图')
                plt.scatter(x[i, :], y[i, :])
                plt.xlabel('phase(degree)')
                plt.ylabel('q')
                plt.title(f'PRPD-{title}')
                # plt.ylim([-0.3 * statistics_limit, statistics_limit * 1.6])
                plt.savefig(self.wave_path[s] + str(i) + title + '.jpg')
                plt.clf()
                plt.close()


if __name__ == '__main__':
    data_path_try = r"D:\DOCU\Seafile\Seafile\MyDocu\NJU\Work\PD_Exp\Data\Try"
    data_try = Prpd(data_path_try)
    data_try_prpd_max, data_try_prpd_max_phase = data_try.prpd_max(200,  50)
    data_try.prpd_plt(data_try_prpd_max, data_try_prpd_max_phase, 'max')



