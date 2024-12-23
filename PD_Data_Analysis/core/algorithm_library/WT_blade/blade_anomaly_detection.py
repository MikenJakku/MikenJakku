import numpy as np
from scipy.signal import stft
from core.CRUD_toolkits.CRUD import CRUD


class BladeDetection:
    def __init__(self, crud: CRUD, **kwargs):

        self.crud = crud  # CRUD工具包
        self.crud.sql_connect(host=kwargs["sql_host"],
                              port=kwargs["sql_port"],
                              user=kwargs["sql_user"],
                              password=kwargs["sql_password"],
                              db_name=kwargs["sql_database"])

    def blade_detect(self, data):
        """
        外部接口：诊断三个叶片
        """
        data = data[:len(data) // self.slice_len * self.slice_len]  # 取整切片数据
        ber_result = self.get_feature(data)
        result = self.classify(ber_result)
        return result, ber_result

    @staticmethod
    def get_feature(self, data):
        return data

    @staticmethod
    def classify(ber_result):
        """
        根据BER结果进行分类
        """
        ber_result = np.array(ber_result)
        level = np.where(ber_result > 1.5)
        return len(level[0])
