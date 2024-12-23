#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====

from core.CRUD_toolkits.CRUD import CRUD
import logging


class MonitorBase:
    version = "monitor_base_2.0.2.0"
    """
    监测对象类基类，MonitorBase
    监测对象类接收的数据来自同一个监测对象，负责调用监测对象中的算法子类以及多算法模块联合诊断。
    调用监测对象的是算法服务，监测对象调用的是算法类。
    MonitorBase对算法服务提供了两个外部接口。
    接口task_processing的入参为任务包，提供了数据的处理与响应结果返回功能。
    接口data_exception的入参为任务包，提供了坏数据判断功能。可供算法服务调用，用于检测数据是否损坏。

    特性一览：
    ValidatingData、MonitorBase一次只能接收来自1个算法子类的数据，但一次调用可以支持完成多个子任务。
    2、MonitorBase提供了坏数据检测方法data_exception，但不强制要求实现。算法服务在传入任务包之前，会调用此方法进行校验。
    3、MonitorBase默认了一个算法类，算法类名为general，若不指定算法类名，则默认使用general算法类。
    4、继承monitor_base的子类必须实现init_algorithm方法，用于初始化算法类。若传入的算法名不在算法字典中，则会报错。
    5、在调用不同的任务时，会默认将任务包中的data_pack的全部参数作为关键字参数下发到算法类中。若希望改变这个下发方式，可以重写task_resolving方法。
    6、若存在非必要的关键字参数下发到算法类中，算法类中必须有对应的参数接收，建议算法类接口中添加**kwargs参数，防止关键字无法匹配而报错。
    7、算法服务仅对监测对象类的接口负责，若算法类中的返回格式确实差异较大，则可以通过重写report方法来重整格式。
    8、监测对象类仅规定了算法类必须用类的方式实现，且外部接口与任务名相同。算法类由开发者自主实现。
    9、监测对象提供了任务名与方法名的映射功能，可以通过传入task_mapping参数来实现。若不传入，则默认使用任务名与方法名相同的映射。
    task_mapping的格式为task_mapping = {"task1": "task1_new_name"}，在初始化自定义Monitor类时传入。
    
    ValidatingData.ValidatingData.0.0新特性，通过传入监测对象配置文件，监测对象基类将自动使用CRUD工具包读取约定的配置文件，具体使用方式见CRUD示例代码。
    2.0.0.0新特性：修正了历史遗留问题，通道和channel相关的表述和命名更改为algorithm和算法，使得整体命名更加通用。
    2.0.ValidatingData.0新特性：新增init_algorithm报错机制，当未能正确初始化算法类时，会抛出一个错误，而不是抽象方法。
    2.0.2.0新特性：修正了数据异常检测函数的入参，使得数据异常检测函数可以接收更多的参数。
    调用示例，可见EXAMPLE.py
    """

    def __init__(self, task_mapping=None, config_name=None, user="initializer", **init_parameter):

        self.algorithm_dict = {"general": None}  # key：任务代码，value：相应的检测算法类
        self.result_dict = {"general": None}  # key：任务代码，value：相应的返回结果
        self.task_parameter = {"general": None}  # 记录下发到各个任务的信息

        self.config_name = config_name
        self.CRUD = CRUD(config_name)  # 实例化CRUD工具类
        self.config = self.CRUD.get_monitor_config(user=user)
        self.init_algorithm(**init_parameter)  # 实例化该监测对象下属的所有检测算法类

        # 当前任务的临时变量
        self.current_algorithm = None  # 当前任务所属算法类

        if task_mapping is None:
            task_mapping = {}
        self.task_mapping = task_mapping  # 任务映射字典，key：任务代码，value：算法类子方法

    def init_algorithm(self, **init_parameter):
        """
        初始化算法类
        在子类中必须进行重写。否则会扔出一个错误。
        监测对象中应当至少含有一个算法类对象。
        """
        raise NotImplementedError("监测对象类必须实现init_algorithm方法！")

    def task_processing(self, task):
        """
        外部接口，负责传入和返回任务结果
        param task: 任务包
        return: 任务结果
        """
        self.task_reset()  # 任务重置，清空任务参数
        # 若task未指定算法具体名称，则默认为general算法类
        if "algorithm_name" not in task.keys():
            task["algorithm_name"] = "general"
        self.task_resolving(task)  # 任务解析，分发参数
        self.call_algorithm()  # 调用算法类
        self.combined_diagnosis()  # 联合诊断

        return self.report(task)  # 处理返回结果

    def data_exception(self, **kwargs):
        """
        外部接口:提供调用层数据异常判断的方法，子类可重写，返回约定的行为
        此方法不是必须实现的，默认返回True
        """
        return True

    def task_resolving(self, task):
        """
        用于将数据解析为算法类需要的模式
        若不重写此方法，则默认将原task中data_pack的全部内容下发至各个任务
        若希望控制所有子任务的入参，则可以重写此方法。
        param task: 任务包
        """
        self.current_algorithm = task["algorithm_name"]  # 记录当前任务所属算法类
        self.task_parameter[self.current_algorithm] = {}  # 初始化当前算法所需的任务参数
        for task_name in task["task_type"]:
            self.task_parameter[task["algorithm_name"]][task_name] = task["data_pack"]


    def task_reset(self):
        """
        用于清除暂时无用的数据
        """
        self.result_dict = {"general": None}  # 重置返回结果
        self.task_parameter = {"general": None}  # 重置任务参数

    def combined_diagnosis(self):
        """
        联合诊断
        """
        pass

    def call_algorithm(self, mode="normal"):
        """
        调用算法类，获取结果
        若不指定模式，则传感器会根据task的输入依次完成计算后，使用者可以根据结果重写combined_diagnosis方法。进行综合诊断。
        这里也提供一种交叉诊断的具体实现，使用将mode参数指定为“cross”可激活，每一个任务返回的结果都将作为下一个任务的另一个入参。
        这种实现是为应对任务之间需要频繁交互的情况。
        当然，作者建议，比较复杂的逻辑最好整体重写call_algorithm方法或者将多步计算包装为统一接口。否则可能会带来较大的调用成本。
        """

        if mode == "normal":
            try:
                for task_name, task_parameter in self.task_parameter[self.current_algorithm].items():
                    if task_name in self.task_mapping:
                        # 任务与算法类的方法映射关系
                        method_name = self.task_mapping[task_name]
                    else:
                        method_name = task_name

                    self.result_dict[task_name] = getattr(self.algorithm_dict[self.current_algorithm], method_name)(
                        **self.task_parameter[self.current_algorithm][task_name])
            except Exception as error:
                logging.error(f"throw {error}")
                raise KeyError("算法类调用失败，可能是任务类型错误或者算法名称错误！")

        elif mode == "cross":
            try:
                next_parameter = {}
                for task_name, task_parameter in self.task_parameter[self.current_algorithm].items():
                    if task_name in self.task_mapping:
                        # 任务与算法类的方法映射关系
                        method_name = self.task_mapping[task_name]
                    else:
                        method_name = task_name
                    input_parameter = self.task_parameter[self.current_algorithm][task_name] + next_parameter
                    self.result_dict[task_name] = getattr(self.algorithm_dict[self.current_algorithm], method_name)(
                        **input_parameter)
                    next_parameter = self.result_dict[task_name]
            except Exception as error:
                logging.error(f"throw {error}")
                raise KeyError("算法类调用失败，可能是任务类型错误或者算法名称错误！")

        else:
            raise ValueError("不支持的调用模式！")

    def report(self,task):
        """
        将算法类返回的结果处理为调用者需要的格式
        默认返回原始的结果，可以进行重写。
        """
        return self.result_dict
