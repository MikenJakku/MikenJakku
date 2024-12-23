import numpy as np
import core.algorithm_frame.signal_processing as signal_processing


feature_dict = {
    "average": None,
    "std": None,
    "variance": None,
    "rms": None,
    "skewness": None,
    "kurtosis": None,
    "pp": None,
    "form_factor": None,
    "crest_factor": None,
    "impulse_factor": None,
    "clearance_factor": None,
    "zero_cross_rate": None,
    "stft": {"frame_length": 256, "hop_length": 128, "window": "hamming", "strict": False}
}

feature_list = [
    "average",
    "std",
    "variance",
    "rms"
]


data = np.random.rand(1000)
result_dict = signal_processing.feature_calculator(data, feature_list)
print(result_dict)
