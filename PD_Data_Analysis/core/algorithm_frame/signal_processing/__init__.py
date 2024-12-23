"""
信号处理方法库
"""
import core.algorithm_frame.signal_processing.feature_calculator as statistical_characteristics


class FeatureCalculator:
    def __init__(self):
        pass

    def method_register(self, method_list=None):
        """
        外部接口：在特征计算工具中注册自定义方法
        :param method_list: 自定义方法列表
        """

        pass

    def __call__(self, data, features=None):
        """
        外部接口，计算信号特征
        :param data: 信号数据
        :param features: 特征列表，若不传入特征列表，则默认计算全部特征。若同时传入了预处理方法，则先对数据进行预处理，再计算特征。
        :return: 特征字典
        """
        result_dict = {}
        # 若自定义特征计算列表，则按照列表计算
        if isinstance(features, (list, set, tuple)):
            for feature_name in features:
                feature_func = getattr(statistical_characteristics, feature_name)
                result_dict[feature_name] = feature_func(data)
        elif isinstance(features, dict):
            # 字典形式的特征列表，feature_name为特征名，parameter_pack为可传递参数
            for feature_name, parameter_pack in features.items():
                feature_func = getattr(statistical_characteristics, feature_name)
                if parameter_pack is not None:
                    result_dict[feature_name] = feature_func(data, **parameter_pack)
                else:
                    result_dict[feature_name] = feature_func(data)

        return result_dict

    def register_method(self, method=None):
        """
        设置自定义方法
        :param method: 自定义方法列表
        """
        # 若method是一个方法，则直接设置
        if callable(method):
            setattr(self, method.__name__, method)
        # 若method是一个实例或对象，则将实例的方法全部设置0
        elif isinstance(method, (object, type)):
            for method_name in dir(method):
                if not method_name.startswith("__"):
                    setattr(self, method_name, getattr(method, method_name))
        # 若method是列表，集合，元祖，字典，则将字典中的方法全部设置
        elif isinstance(method, (list, set, tuple, dict)):
            for method_name, method_func in method.items():
                setattr(self, method_name, method_func)
        else:
            raise ValueError("未识别的method类型")


feature_calculator = FeatureCalculator()
