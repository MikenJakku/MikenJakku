import os
import pandas as pd
from core.CRUD_toolkits.CRUD import CRUD

algorithm_config_dir = r"../algorithm_config"
ledger_file = "../../http_service/config_file/ledger.csv"
# 清空台账文件
if os.path.exists(ledger_file):
    os.remove(ledger_file)

print('清空台账文件')
# 根据配置文件信息生成表
for config_name in os.listdir(algorithm_config_dir):
    if not config_name.endswith(".json"):
        continue
    if not (config_name.startswith("PD") or config_name.startswith("EXAMPLE")
            or config_name.startswith("BYQ") or config_name.startswith("Thresholding")): #
        continue
    print(config_name)
    crud = CRUD(config_name)
    config = crud.get_monitor_config(user="server")
    for algorithm_name in config.task_pack:
        algorithm_tasks = config.task_pack[algorithm_name]
        for task_type in algorithm_tasks:
            task = algorithm_tasks[task_type]
            description = task["description"]
            for function_name in description:
                tag_list = description[function_name]
                for tag in tag_list:
                    data = {
                        "tag": tag,
                        "function": function_name,
                        "monitor": config.monitor_name,
                        "algorithm": algorithm_name,
                        "task": task_type
                    }
                    df = pd.DataFrame(data, index=[0])
                    if os.path.exists(ledger_file):
                        df.to_csv(ledger_file, mode="a", header=False, index=False)
                    else:
                        df.to_csv(ledger_file, mode="w", header=True, index=False)
# 读取台账文件第一列的信息
df = pd.read_csv(ledger_file)
tag_list = df["tag"].tolist()
if len(tag_list) != len(set(tag_list)):
    raise Exception("台账文件中存在重复的tag信息，请检查！")

print("台账信息生成成功！")
