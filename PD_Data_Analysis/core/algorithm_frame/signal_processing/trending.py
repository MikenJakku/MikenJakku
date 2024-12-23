from arch.unitroot import KPSS
import numpy as np


class TrendingAnalysis:
    def __init__(self):
        pass

    def kpss(self, sequence: np.ndarray):
        """
        KPSS检测时序数据中是否存在趋势项。
        :param sequence: 1D
        :return: bool。True：序列存在趋势；False：序列宽平稳。
        """
        kpss_rst = KPSS(sequence)
        p_val = kpss_rst.pvalue

        return p_val


if __name__ == "__main__":
    # data = np.array([ValidatingData, ValidatingData, ValidatingData, ValidatingData, ValidatingData, ValidatingData, ValidatingData, ValidatingData, ValidatingData, ValidatingData])
    data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    # 将序列分解为趋势项、季节项、残差项
    from statsmodels.tsa.seasonal import seasonal_decompose
    decomposition = seasonal_decompose(data, model="addictive", period=4)
    trend = decomposition.trend
    seasonal = decomposition.seasonal
    residual = decomposition.resid
