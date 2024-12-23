import os
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf
from scipy.signal import hilbert, butter, filtfilt
from matplotlib import rcParams


class EnvSpec:
    def __init__(self, data_path):
        self.wave_path = []
        for roots, dirs, files in os.walk(data_path):
            if len(files) > 0:
                for file_ in files:
                    if os.path.splitext(file_)[1] == '.wav':
                        # 数据目录读取
                        self.wave_path.append(os.path.join(roots, file_))

    def envelope(self, t):
        wave_env_set = []
        wave_env_fft_set = []
        for s in range(len(self.wave_path)):
            # 数据读取 + 预处理
            wave_path_s = self.wave_path[s]
            wave_s, sr = sf.read(wave_path_s)
            wave_s /= np.max(wave_s)
            if len(wave_s.shape) > 1:
                wave_s = wave_s[:, 0]
            wave_s = wave_s[:int(sr*t)]
            b, a = butter(8, 0.01, 'highpass')
            wave_s = filtfilt(b, a, wave_s)
            # 包络提取
            wave_env = np.abs(hilbert(wave_s))
            wave_env -= np.mean(wave_env)
            wave_env_fft = np.abs(np.fft.rfft(wave_env))
            wave_env_set.append(wave_env)
            wave_env_fft_set.append(wave_env_fft)
            print(f'第{s}段音频计算')
        f_scale = np.linspace(0, sr/2, len(wave_env_fft_set[0]))
        return wave_env_set, wave_env_fft_set, f_scale

    def env_fft_plt(self, wave_env_fft_set, x, top_fre):
        config = {
            "font.family": 'Times New Roman',
        }
        rcParams.update(config)
        for s in range(len(self.wave_path)):
            print(f'第{s}段音频')
            y = wave_env_fft_set[s]
            plt.plot(x[:top_fre], y[:top_fre], color='r')
            plt.xlabel('Frequency (Hz)')
            plt.ylabel('Amplitude')
            plt.title('Envelope_FFT', fontsize=15)
            plt.savefig(self.wave_path[s] + str(s) + '.jpg', dpi=300)
            plt.clf()
            plt.close()


if __name__ == '__main__':
    data_try_path = r"D:\WORK\DOCU\Seafile\MyDocu\NJU\Work\Partial Discharge\Data\临汾"
    data_try = EnvSpec(data_try_path)
    _, data_try_env_spec, f_scale = data_try.envelope(2)
    data_try.env_fft_plt(data_try_env_spec, f_scale, 800)

