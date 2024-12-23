import os
import soundfile as sf
from tqdm import tqdm

from core.CRUD_toolkits.CRUD import CRUD
from ber_calculator import ber_calculate


def data_loader(data_dir) -> tuple:
    """
    :param data_dir: 数据文件夹
    :return: wav数据
    """

    for wav_name in os.listdir(data_dir):
        if not wav_name.endswith(".wav"):
            continue
        wav_split = wav_name[:-4].split("-")
        channel_name = wav_split[0]
        wav_time = wav_split[1] + "-" + wav_split[2] + "-" + wav_split[3] +\
            " " + wav_split[4] + ":" + wav_split[5] + ":" + wav_split[6]
        wav_path = os.path.join(data_dir, wav_name)
        try:
            data, sr = sf.read(wav_path)
            yield channel_name, wav_time, data, sr
        except Exception as e:
            yield None, None, None, None


def main():
    crud = CRUD()
    crud.sql_connect(host='192.168.3.101', port=3306, user='root', password='root123', db_name='blade_test')
    org_data_dir = r"\\192.168.3.80\算法\声纹-算法\叶片数据\正常叶片2\P10054"
    data_generator = data_loader(org_data_dir)

    for channel_name, wav_time, data, sr in data_generator:
        print(wav_time)
        if data is None:
            continue
        data = data[::2]
        ber_result = ber_calculate(data, check=False)
        # 取小数点后两位序列化
        ber_result = [round(i, 2) for i in ber_result]
        ber_str = ",".join([str(i) for i in ber_result])
        channel_name = "36_P10054"
        try:
            crud.sql_tools.add_info(channel_name, [wav_time, ber_str])
        except Exception as e:
            print(e)

    pass


if __name__ == "__main__":
    main()
