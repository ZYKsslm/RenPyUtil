# 此文件提供了一系列基于Ren'Py的功能类，以供Ren'Py开发者调用
# 作者  ZYKsslm
# 仓库  https://github.com/ZYKsslm/RenPyUtil
# 声明  该源码使用 MIT 协议开源，但若使用需要在程序中标明作者信息


# 对话组使用的transform
"""renpy
define config.rollback_enabled = False

transform emphasize(t, l):
    linear t matrixcolor BrightnessMatrix(l)
"""

"""renpy
init -1 python:
"""


import random
from typing import Callable
from functools import partial

renpy = renpy # type: ignore
config = config # type: ignore


class CharacterError(Exception):
    """该类为一个异常类，用于检测角色对象。"""

    errorType = {
        "typeError": "对象类型错误，应为AdvancedCharacter而非{}！",
        "imageTagError": "{}角色未绑定图像标签，无法支持强调！",
        "handlerError": "handler必须为jump或call，而非{}！",
        "labelArgsError": "用于跳转的脚本标签{}无法传递参数！",
    }

    def __init__(self, error_type, *args):
        super().__init__()
        self.error_type = error_type
        self.args = args

    def __str__(self):
        return CharacterError.errorType[self.error_type].format(*self.args)


class CharacterTask:
    """该类为角色任务类，用于高级角色对象绑定任务。"""        

    def __init__(self, single_use=True, priority=0):
        
        """初始化一个任务。
        
        Keyword Arguments:
            single_use -- 该任务是否只执行一次。 (default: {True})
            priority -- 任务优先级。 (default: {0})
        """            

        self.single_use = single_use
        self.priority = priority
        self.condition_list: list[str] = []
        self.func_list = []
        self.label = None

    def add_condition(self, exp: str, *args):
        """调用该方法，给任务添加一个条件。

        Example:
            task.add_condition("{health} < 50", "health")
        """        

        condition = exp.format_map({arg: f"CHARACTER.{arg}" for arg in args})
        self.condition_list.append(condition)

    def set_label(self, label: str, handler="call", *args, **kwargs):
        """调用该方法，给任务绑定一个脚本标签。当条件满足时，将跳转或调用该脚本标签。

        Arguments:
            label -- 脚本标签名。
        
        Keyword Arguments:
            handler -- 标签处理方式。必须为 `jump` 或 `call`。 (default: {"call"})

        不定参数为标签参数。
        """

        if handler not in ("jump", "call"):
            raise CharacterError("handlerError", handler)
        
        if handler == "jump":
            if args or kwargs:
                raise CharacterError("labelArgsError", label)
            task_label = partial(renpy.jump, label)
        else:
            task_label = partial(renpy.call, label, *args, **kwargs)
        
        self.label = task_label

    def add_func(self, func: Callable, *args, **kwargs):
        """调用该方法，给任务添加一个函数。当条件满足时，该函数将被执行。该函数的返回值将被忽略。
        
        Arguments:
            func -- 一个函数。

        Keyword Arguments:
            name -- 该函数的名称。 (default: {None})

        不定参数为函数参数。
        """        

        self.func_list.append(partial(func, *args, **kwargs))


class AdvancedCharacter(ADVCharacter): # type: ignore
    """该类继承自ADVCharacter类，在原有的基础上增添了一些新的属性和方法。"""

    def __init__(self, name=None, kind=None, **properties):
        """初始化方法。若实例属性需要被存档保存，则定义对象时请使用`default`语句或Python语句。

        Keyword Arguments:
            name -- 角色名。 (default: {NotSet})
            kind -- 角色类型。 (default: {None})
        """

        if not name:
            name = renpy.character.NotSet

        self.task_list: list[CharacterTask] = []
        super().__init__(name=name, kind=kind, **properties)

    def _emphasize(self, emphasize_callback, t, l):
        """使角色对象支持强调。"""

        if self.image_tag:
            self.display_args["callback"] = partial(emphasize_callback, self, t=t, l=l)
        else:
            raise CharacterError("imageTagError", self.name)

    def add_task(self, task: CharacterTask):
        """调用该方法，绑定一个角色任务。

        Arguments:
            task -- 一个角色任务。
        """            

        self.task_list.append(task)
        if self._check_task not in config.python_callbacks:
            config.python_callbacks.append(self._check_task)

    def setter(self, **attrs):
        """调用该方法，给该角色对象创建自定义的一系列属性。"""

        for a, v in attrs.items():
            setattr(self, a, v)

    def _check_task(self):
        """该方法用于在更新自定义属性值时触发任务。"""

        if not self.task_list:
            return
        
        self.task_list.sort(key=lambda x: x.priority, reverse=True)

        satisfied_task: list[CharacterTask] = []
        for task in self.task_list:
            all_conditions_met = True
            for condition in task.condition_list:
                if not eval(condition, {"CHARACTER": self}):
                    all_conditions_met = False
                    break

            if not all_conditions_met:
                continue
            
            if task.label:
                task.label()

            satisfied_task.append(task)

        for task in satisfied_task:
            for task_func in task.func_list:
                task_func()

            if task.single_use:
                self.task_list.remove(task)


class CharacterGroup:
    """该类用于管理多个高级角色对象。"""

    def __init__(self, *characters: AdvancedCharacter):
        """初始化方法。"""

        self.character_group: list[AdvancedCharacter] = []
        self.add_characters(*characters)
        self.task_list: list[CharacterTask] = []
        self.attr_list = set()

    @staticmethod
    def  _check_type(obj):
        """检查对象类型。"""        

        if isinstance(obj, AdvancedCharacter):
            return
        raise CharacterError("typeError", type(obj).__name__)

    def add_characters(self, *characters: AdvancedCharacter):
        """调用该方法，向角色组中添加一个或多个角色对象。"""

        for character in characters:
            CharacterGroup._check_type(character)
            self.character_group.append(character)
         
    def get_random_character(self, rp=True):
        """调用该方法，返回角色组中随机一个角色对象。

        Keyword Arguments:
            rp -- 是否使用`renpy`随机接口。 (default: {True})
        """        

        choice = renpy.random.choice if rp else random.choice # type: ignore
        
        return choice(list(self.character_group))

    def del_characters(self, *characters: AdvancedCharacter):
        """调用该方法，删除角色组中的一个或多个角色。"""
        
        for character in characters:
            CharacterGroup._check_type(character)
            self.character_group.remove(character)

    def setter(self, **kwargs):
        """调用该方法，对角色组中所有角色对象创建自定义的一系列属性。

        Example:
            character_group.add_group_attr(strength=100, health=100)
        """

        self.attr_list |= set(kwargs.keys())

        for character in self.character_group:
            character.setter(**kwargs)

    def getter(self, name, rp=True):
        """调用该方法，获取角色组中所有角色的指定属性值。当属性值冲突时，随机返回。

        Keyword Arguments:
            name -- 属性名。
            rp -- 随机返回是否使用`renpy`随机接口。 (default: {True})
        """

        return _ChrAttrGetter(self, name, rp).getter()

    def add_task(self, task: CharacterTask):
        """调用该方法，给角色组添加一个任务，所有角色都满足条件才会触发。"""

        self.task_list.append(task)
        if self._check_task not in config.python_callbacks:
            config.python_callbacks.append(self._check_task)
    
    def _check_task(self):
        """该方法用于在角色组中所有角色属性值更新时触发任务。"""

        if not self.task_list:  
            return
        
        self.task_list.sort(key=lambda x: x.priority, reverse=True)

        satisfied_task: list[CharacterTask] = []
        for task in self.task_list:
            all_conditions_met = True
            for character in self.character_group:
                for condition in task.condition_list:
                    if not eval(condition, {"CHARACTER": character}):
                        all_conditions_met = False
                        break
                
                if not all_conditions_met:
                    break

            if not all_conditions_met:
                continue
            
            if task.label:
                task.label()
            
            satisfied_task.append(task)

        for task in satisfied_task:
            for task_func in task.func_list:
                task_func()

            if task.single_use:
                self.task_list.remove(task)

    def __getattr__(self, name):
        if name in ("character_group", "task_list", "attr_list", "t", "l", "started"):
            return getattr(self, name)

        return _ChrAttrSetter(self, name)
    
    def __setattr__(self, name, value):
        if name in ("character_group", "task_list", "attr_list", "t", "l", "started"):
            return super().__setattr__(name, value)
        
        if value == None:
            return
        
        return self.setter(**{name: value})


class _ChrAttrGetter:
    def __init__(self, character_group: CharacterGroup, name, rp):
        self.character_group = character_group
        self.name = name
        self.rp = rp
        
    def getter(self):
        values = set([getattr(character, self.name) for character in self.character_group.character_group])
        if len(values) == 1:
            return values.pop()
        choice = renpy.random.choice if self.rp else random.choice

        return choice(list(values))
    

class _ChrAttrSetter:
    def __init__(self, character_group: CharacterGroup, name):
        self.character_group = character_group
        self.name = name
        
    def _apply_operation(self, op, value):
        for character in self.character_group.character_group:
            setattr(character, self.name, op(getattr(character, self.name), value))

        return None

    def __iadd__(self, value):
        return self._apply_operation(lambda a, b: a + b, value)

    def __isub__(self, value):
        return self._apply_operation(lambda a, b: a - b, value)

    def __imul__(self, value):
        return self._apply_operation(lambda a, b: a * b, value)

    def __itruediv__(self, value):
        return self._apply_operation(lambda a, b: a / b, value)

    def __ifloordiv__(self, value):
        return self._apply_operation(lambda a, b: a // b, value)
    
    def __imod__(self, value):
        return self._apply_operation(lambda a, b: a % b, value)

    def __ipow__(self, value):
        return self._apply_operation(lambda a, b: a ** b, value)


class SpeakingGroup(CharacterGroup):
    """该类继承自CharacterGroup类，用于管理角色发言组。"""

    def __init__(self, *characters: AdvancedCharacter, t=0.15, l=-0.3):
        """初始化方法。
        
        Arguments:
            t -- 转变的时长 (default: {0.15})
            l -- 变暗的明度。 (default: {-1})
        """
        
        self.t = t
        self.l = l
        self.started = True
        super().__init__(*characters)

    def start(self):
        """调用该方法，开始进入发言强调状态。"""

        self.started = True

    def end(self):
        """调用该方法，结束发言强调状态。"""

        self.started = False

    def add_characters(self, *characters: AdvancedCharacter):
        for character in characters:
            CharacterGroup._check_type(character)
            character._emphasize(self.emphasize, self.t, self.l)    # 使角色支持强调
            self.character_group.append(character)

    def del_characters(self, *characters):
        for character in characters:
            CharacterGroup._check_type(character)
            character.display_args["callback"] = None
            self.character_group.remove(character)

    def emphasize(self, character: AdvancedCharacter, event, t=0.15, l=-0.3, **kwargs):
        """该方法用于定义角色对象时作为回调函数使用。该方法可创建一个对话组，对话组中一个角色说话时，其他角色将变暗。"""            

        if (not event == "begin") or (not self.started):
            return

        if character not in self.character_group:
            self.add_characters(character)
        
        image = renpy.get_say_image_tag()
        if renpy.showing(character.image_tag):
            renpy.show(
                image, 
                at_list=[emphasize(t, 0)] # type: ignore
            )
        
        for speaker in self.character_group:
            if speaker != character and renpy.showing(speaker.image_tag):
                renpy.show(
                    speaker.image_tag, 
                    at_list=[emphasize(t, l)] # type: ignore
                )

