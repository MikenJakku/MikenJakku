#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====

import datetime
import time


def time_this(func):
    """
    函数计时器
    """

    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(func.__name__, "used", str(end_time - start_time) + "s")
        return result

    return wrapper


def date2jd(date):
    # 日期转简约儒略日
    date = datetime.datetime.strptime(date, "%Y-%m-%d-%H-%M-%S-%f")
    jd = date.toordinal() \
         + 1721425.5 + date.hour / 24 + date.minute / 1440 + date.second / 86400 + date.microsecond / 86400000000
    sjd = jd - 2400000.5
    return sjd


def jd2date(sjd):
    # 儒略日转日期
    sjd = sjd + 2400000.5 - 1721425.5
    date_hour = int((sjd - int(sjd)) * 24)
    date_minute = int(((sjd - int(sjd)) * 24 - date_hour) * 60)
    date_second = int((((sjd - int(sjd)) * 24 - date_hour) * 60 - date_minute) * 60)
    date_microsecond = int(((((sjd - int(sjd)) * 24 - date_hour) * 60 - date_minute) * 60 - date_second) * 1000000)
    date = datetime.datetime.fromordinal(int(sjd)) + datetime.timedelta(days=int(sjd % 1), hours=date_hour,
                                                                        minutes=date_minute,
                                                                        seconds=date_second,
                                                                        microseconds=date_microsecond)
    return date


if __name__ == "__main__":
    date_now = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    print("now:", date_now)
    sjd_test1 = date2jd(date_now)
    print("now_sjd", sjd_test1)
