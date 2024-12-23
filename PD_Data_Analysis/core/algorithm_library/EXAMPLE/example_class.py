class example_class:
    def __init__(self, CRUD, **kwargs):
        self.CRUD = CRUD

    @staticmethod
    def task1(scenario, **kwargs):
        print(f"task1传入scenario参数:{scenario},{kwargs}")
        return {'result':"*2"}

    @staticmethod
    def task2(sample_rate, **kwargs):
        print(f"task2传入sample_rate参数:{sample_rate},{kwargs}")
        return {'result':"*0"}

    @staticmethod
    def task3(sample_rate,scenario,equipment_id, **kwargs):
        print(f"task3传入sample_rate,scenario参数:{sample_rate},{scenario},{equipment_id},{kwargs}")
        return {'result':"*ValidatingData"}