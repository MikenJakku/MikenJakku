from core.CRUD_toolkits.CRUD import CRUD
import numpy as np
from tqdm import tqdm

monitor_config_name = "EXAMPLE.json"
crud = CRUD(monitor_config_name)


def register(equipment_id):
    """
    注册器测试用例
    """

    crud.equipment_register(equipment_id)


def data_persistence():
    """
    数据持久化测试用例
    """

    equipment_id = "TXKJ-0001"
    data_pack = {
        "pp": np.random.rand(1000).tolist(),
        "db": np.random.rand(1).tolist(),
    }
    for _ in tqdm(range(300)):
        data_pack["pp"] = np.random.rand(1000).tolist()
        crud.data_storage_time_series(equipment_id, data_pack)

    read_data = crud.data_read_time_series(equipment_id, "2023-08-17-20-16-59-524573")
    pass


if __name__ == "__main__":
    # register(equipment_id='TXKJ-0001')

    data_persistence()
