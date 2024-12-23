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

    def prpd_max(self, fixed_frame_num, point_num, phase_num):
        """
        计算数据集的PRPD(最大值）
        :param fixed_frame_num: 指定的画图帧数
        :param point_num: 重复打点数，point_num为每个窗口所打点的数量，实际上也是每张PRPD图所包含的工频周期数,每个相位窗口的实际采样点数取决于采样率，因此mean和max都是有意义的
        :param phase_num: 相位窗口数，影响每一工频周期内的采样率
        :return:  一个list：prpd_max_set，每个元素代表每个文件生成的多张PRPD图（PRPD图实质上是一维数组，因此返回list的每个元素是一个二维数组 帧数*长度）
        """
        prpd_max_set = []
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
            pd_len = int(sr * t)
            frame_point_num = int(pd_len * point_num)
            if fixed_frame_num <= int(len(wave_s) // frame_point_num):
                frame_num = fixed_frame_num
            else:
                frame_num = int(len(wave_s) // frame_point_num)
            phase_len = pd_len // phase_num
            prpd_max = np.zeros((frame_num, int(phase_num * point_num)))
            for i in range(frame_num):
                prpd_i = wave_s[i*frame_point_num: (i+1)*frame_point_num]
                for j in range(point_num):
                    prpd_i_j = prpd_i[j*pd_len: (j+1)*pd_len]
                    for k in range(phase_num):
                        prpd_i_j_k = prpd_i_j[k*phase_len: (k+1)*phase_len]
                        index = np.argmax(np.abs(prpd_i_j_k))
                        prpd_max[i, k*point_num+j] = prpd_i_j_k[index]
            prpd_max_set.append(prpd_max)
            print(f'音频PRPD维度：{prpd_max.shape}')
        return prpd_max_set

    def prpd_mean(self, fixed_frame_num, point_num, phase_num):
        """
        计算音频的q_mean-n(PRPD)
        :param fixed_frame_num: 同上
        :param point_num: 同上，取点方式为取平均
        :param phase_num: 同上
        :return:
        """
        prpd_mean_set = []
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
            pd_len = 1 * int(sr*t)
            frame_point_num = int(pd_len * point_num)
            if fixed_frame_num <= int(len(wave_s) // frame_point_num):
                frame_num = fixed_frame_num
            else:
                frame_num = int(len(wave_s) // frame_point_num)
            phase_len = pd_len // phase_num
            prpd_mean = np.zeros((frame_num, int(phase_num * point_num)))
            for i in range(frame_num):
                prpd_i = wave_s[i*frame_point_num: (i+1)*frame_point_num]
                for j in range(point_num):
                    prpd_i_j = prpd_i[j*pd_len: (j+1)*pd_len]
                    for k in range(phase_num):
                        prpd_i_j_k = prpd_i_j[k*phase_len: (k+1)*phase_len]
                        prpd_mean[i, k*point_num+j] = np.mean(prpd_i_j_k)
            prpd_mean_set.append(prpd_mean)
            print(f'第{s}段音频PRPD维度：{prpd_mean.shape}')
        return prpd_mean_set

    def prpd_plt(self, prpd_set, point_num, title, phase_num):
        """
        PRPD的画图方法
        :param prpd_set: 输入的PRPD数据
        :param point_num: 计算PRPD数据时选择的打点数
        :param title: PRPD类型，用于生成文件名
        :param phase_num: 相位窗口数，用于生成相位索引
        :return: 在文件源路径生成对应的PRPD图并保存
        """
        frame_point_num = prpd_set[0].shape[1]
        phase = np.zeros(frame_point_num)
        print(frame_point_num, point_num)
        for p in range(frame_point_num):
            phase[p] = int((p // point_num) + 1)
        print(phase)
        config = {
            "font.family": 'Times New Roman',
        }
        rcParams.update(config)
        for s in range(len(self.wave_path)):
            frame_num = prpd_set[s].shape[0]
            y = prpd_set[s]
            statistics_limit = np.percentile(np.sort(np.abs(y)), 99)
            for i in range(frame_num):
                print(f'第{s}段音频第{1+i}张图')
                plt.scatter(phase, np.abs(y[i, :]), s=10)
                plt.xticks(np.array([90, 180, 270, 360])*phase_num/360, np.array([90, 180, 270, 360]))
                plt.xlabel('phase(degree)')
                plt.ylabel('q')
                plt.title(f'PRPD-{title}')
                # print(np.isnan(y))
                plt.ylim([-0.3*statistics_limit, statistics_limit*2.6])
                # plt.ylim([-0.1, 0.3])
                plt.savefig(self.wave_path[s] + str(i) + title + '.jpg', dpi=300)
                plt.clf()
                plt.close()


if __name__ == '__main__':
    data_try_path = r"D:\WORK\DOCU\Seafile\MyDocu\NJU\Work\Partial Discharge\Data\重庆"
    data_try = Prpd(data_try_path)
    # data_try_prpd_max = data_try.prpd_max(3,  1, 1800)
    # data_try.prpd_plt(data_try_prpd_max, 1, 'max', 1800)

    data_try_prpd_mean = data_try.prpd_mean(5, 3, 720)
    data_try.prpd_plt(data_try_prpd_mean, 3, 'mean', 720)


