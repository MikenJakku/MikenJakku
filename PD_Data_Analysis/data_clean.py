import os


class Clean:
    def __init__(self, data_path):
        self.wave_path = []
        for roots, dirs, files in os.walk(data_path):
            if len(files) > 0:
                for file_ in files:
                    file_path = os.path.join(roots, file_)
                    if os.path.splitext(file_)[1] != '.wav':
                        try:
                            os.remove(file_path)  # 删除文件
                            print(f"Deleted: {file_}")
                        except Exception as e:
                            print(f"Failed to delete {file_}: {e}")
                    else:
                        self.wave_path.append(file_path)  # 保存.wav文件路径


data_try_path = r"\\192.168.3.33\data_suanfa\JF23057-柱上配变\GP\无人机\Labelled_Data"
cleaner = Clean(data_try_path)
