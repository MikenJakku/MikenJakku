from core.algorithm_library.EXAMPLE.example_class import example_class
from core.algorithm_frame.base_class.monitor_base import MonitorBase
import logging

class EXAMPLEMonitor(MonitorBase):
    def init_algorithm(self):
        """
        初始化算法类
        抽象方法，在子类中必须进行实现。监测对象中应当至少含有一个算法类对象。
        """
        # 可以通过此方式，将CRUD工具库实例传递至算法类。这样做的好处是不必在算法类中考虑CRUD工具库的变动。由框架统一维护。
        algorithm_config_dict = self.config.__dict__
        algorithm_config_dict.update({"CRUD": self.CRUD})

        # 在此定义各算法algorithm的实现方式，记录于self.algorithm_dict[algorithm]
        # example_class中的静态方法def task_x 成为属性task_x —— 这是一种很便捷的方式，赞+ValidatingData
        self.algorithm_dict["algorithm1"] = example_class(**algorithm_config_dict)
        self.algorithm_dict["algorithm2"] = example_class(**algorithm_config_dict)

    def report(self,task):
        """
        将算法类返回的结果处理为调用者需要的格式
        默认返回原始的结果，可以进行重写。
        """
        ###--- 在这里不要出现获取label_mapping， label_mapping应出现montor_server --- ###
        # 实现一个重写示例
        logging.debug(' monitor_result before report() = {}'.format(self.result_dict))
        for task_type in task["task_type"]:
            # 算法class计算的初始标签
            result_cotent = self.result_dict[task_type]["result"]
            # 新标签
            result_cotent_new = result_cotent.replace("*","")
            self.result_dict[task_type]["result"] = result_cotent_new

        return self.result_dict

def task_example():
    task_pack = {
        'task_type': ["task1", "task2"], # 算法类是支持多task的，但服务实现时在request_parsing.py中已通过for循环将每个task单独处理
        'algorithm_name': "algorithm1",
        'data_pack': {
            'scenario': "开关柜",
            'sample_rate': 96000,
            'data': [1, 2, 3]
        }
    }

    example_monitor = EXAMPLEMonitor(config_name="EXAMPLE.json")
    result = example_monitor.task_processing(task=task_pack)
    print(f'result = {result}')


if __name__ == "__main__":
    task_example()
