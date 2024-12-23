import os
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf
from scipy.signal import hilbert, butter, filtfilt
from matplotlib import rcParams


class Data:
    def __init__(self, data_path):
        for roots, dirs, files in os.walk(data_path):
            if len(files) > 0:
                i = 0
                for file_ in files:
                    i += 1
                    if os.path.splitext(file_)[1] == '.wav':
                        # 读取文件 + 预处理
                        data_path = os.path.join(roots, file_)
                        wave, sr = sf.read(data_path)
                        print(wave.shape, sr)
                        if len(wave.shape) > 1:
                            wave = wave[:int(sr * 1), 0]
                        else:
                            wave = wave[:int(sr * 1)]
                        t = len(wave) / sr
                        b, a = butter(8, 0.05, 'highpass')
                        wave = filtfilt(b, a, wave)
                        frame_len = hop_len = 128
                        # 画图设置
                        config = {
                            "font.family": 'Times New Roman',  # 设置字体类型
                            # "font.family": 'MicroSoft YaHei',  # 设置字体类型
                        }
                        rcParams.update(config)
                        plt.figure(figsize=(17, 13))

                        # wave
                        plt.subplot(2, 2, 1)
                        plt.plot(np.linspace(0, t, len(wave)), wave)
                        plt.ylabel('Amplitude', fontsize=13, labelpad=10)
                        plt.xlabel('Time (s)', fontsize=13)
                        plt.title('wave', fontsize=15)
                        # stft
                        wave_spec = np.abs(librosa.stft(y=wave, n_fft=frame_len, hop_length=hop_len))
                        plt.subplot(2, 2, 2)
                        librosa.display.specshow(librosa.power_to_db(wave_spec, ref=np.max), cmap='jet', vmin=-80,
                                                 sr=sr, x_axis='time', y_axis='hz', hop_length=hop_len)
                        plt.ylabel('Frequency (Hz)', fontsize=13, labelpad=10)
                        plt.xlabel('Time (s)', fontsize=13)
                        plt.title('STFT', fontsize=15)
                        # hilbert
                        plt.subplot(2, 2, 3)
                        env_wave = np.abs(hilbert(wave))
                        env_wave = env_wave - np.mean(env_wave)
                        plt.plot(np.linspace(0, t, len(wave)), env_wave)
                        plt.ylabel('Amplitude', fontsize=13, labelpad=10)
                        plt.xlabel('Time (s)', fontsize=13)
                        plt.title('Hilbert', fontsize=15)
                        # hilbert_fft
                        plt.subplot(2, 2, 4)
                        wave_fft = np.abs(np.fft.rfft(env_wave))
                        f_scale = np.linspace(0, sr/2, len(wave_fft))
                        plt.plot(f_scale[:1000], wave_fft[:1000])
                        plt.ylabel('Amplitude', fontsize=13, labelpad=10)
                        plt.xlabel('Frequency (Hz)', fontsize=13)
                        plt.title('Hilbert_FFT', fontsize=15)
                        plt.savefig(os.path.join(roots, file_) + str(i) + '.jpg', dpi=300)
                        plt.clf()
                        plt.close()
                        # plt.show()


if __name__ == '__main__':
    file_path = r"D:\DOCU\Seafile\Seafile\MyDocu\NJU\Work\PD_Exp\Data\Try"
    data_show = Data(file_path)
