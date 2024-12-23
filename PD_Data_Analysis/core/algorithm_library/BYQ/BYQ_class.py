from .feature_extraction import  FeatureExtraction
from .anomaly_detection import AnomalyDetection
from .trend_monitor import TrendMonitor


class BYQClass:
    """
    变压器算法
    """
    def __init__(self):
        """初始化参数"""
        pass

    @staticmethod
    def real_time_feature_extraction(**kwargs):
        """实时特征提取"""
        feature_tool = FeatureExtraction(kwargs['sample_rate'])  # 特征提取类实例
        feature_result = feature_tool.forward(kwargs['data'])
        return feature_result

    @staticmethod
    def anomaly_detection(**kwargs):
        """异常检测"""
        detection_tool = AnomalyDetection()  # 异常检测类实例
        result = detection_tool.forward(**kwargs)
        return result

    @staticmethod
    def real_time_BYQ_anomaly_detection(**kwargs):
        """实时异常检测，传入一段数据，针对整段数据进行异常检测"""
        feature_tool = FeatureExtraction(kwargs['sample_rate'])
        feature_result = feature_tool.forward(kwargs['data'])
        # print(feature_result)
        detection_tool = AnomalyDetection()
        result = detection_tool.forward(**feature_result)
        # print(self.result)
        return result

    @staticmethod
    def trend_monitoring(**kwargs):
        """长期趋势监测"""
        trend_tool = TrendMonitor()  # 长期趋势监测类实例
        trend_result = trend_tool.forward(**kwargs)
        return trend_result
