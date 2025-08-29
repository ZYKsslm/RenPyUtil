# 描述  角色任务类
# 作者  ZYKsslm
# 仓库  https://github.com/ZYKsslm/RenPyUtil
# 声明  该源码使用 MIT 协议开源，但若使用需要在程序中标明作者信息


import re

from typing import Callable
from functools import partial

import renpy.exports as renpy # type: ignore


class CharacterTask:
    """该类为角色任务类，用于高级角色对象绑定任务。"""        

    def __init__(self, single_use=True, priority=0):
        
        """初始化一个任务。
        
        :param single_use: 该任务是否只执行一次
        :param priority: 任务优先级
        """            

        self.single_use = single_use
        self.priority = priority
        self.condition_list: list[str] = []
        self.func_list = []

        self.required_attrs = set()

    def add_condition(self, exp: str):
        """调用该方法，给任务添加一个条件。

        Args:
            exp: 条件表达式

        Examples:
            ```
            # {health} 表示角色对象的 health 属性
            task.add_condition("{health} < 50")
            ```
        """

        args = re.findall(r"\{(\w+)\}", exp)

        condition = exp.format_map({arg: f"CHARACTER.{arg}" for arg in args})
        self.condition_list.append(condition)
        self.required_attrs.update(args)

    def add_func(self, func: Callable, *args, **kwargs):
        """调用该方法，给任务添加一个函数。当条件满足时，该函数将被执行。该函数的返回值将被忽略。
        
        Args:
            func: 要执行的函数
            args: 传递给函数的参数
            kwargs: 传递给函数的关键字参数

        Examples:
            ```
            def task_func(*args, **kwargs):
                ...
                
            task.add_func(task_func, *args, **kwargs)
            ```
        """        

        self.func_list.append(partial(func, *args, **kwargs))