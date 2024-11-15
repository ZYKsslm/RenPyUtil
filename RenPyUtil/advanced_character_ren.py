# 此文件提供了一系列基于Ren'Py的功能类，以供Ren'Py开发者调用
# 作者  ZYKsslm
# 仓库  https://github.com/ZYKsslm/RenPyUtil
# 声明  该源码使用 MIT 协议开源，但若使用需要在程序中标明作者信息


# 对话组使用的transform
"""renpy
transform emphasize(t, l):
    linear t matrixcolor BrightnessMatrix(l)
"""

"""renpy
init -1 python:
"""


import random
from functools import partial


def threading_task(func):
    """一个装饰器，被装饰的函数将在子线程中运行。
    
    被装饰的函数使用`Ren'Py API`能做到事情非常有限，通常用来调用`renpy.notify()`函数或实时更新变量。

    Arguments:
        func -- 一个函数。
    """        

    def wrapper(*args, **kwargs):
        renpy.invoke_in_thread(func, *args, **kwargs) # type: ignore
        
    return wrapper


class CharacterError(Exception):
    """该类为一个异常类，用于检测角色对象。"""

    errorType = {
        0: "错误地传入了一个ADVCharacter类，请传入一个AdvancedCharacter高级角色类！",
        1: "对象类型错误!",
        2: "该角色对象不在角色组内！",
        3: "该角色对象无图像标签，无法强调！"
    }

    def __init__(self, errorCode):
        super().__init__()
        self.errorCode = errorCode

    def __str__(self):
        return CharacterError.errorType[self.errorCode]


class CharacterTask(object):
    """该类为角色任务类，用于高级角色对象绑定任务。"""        

    def __init__(self, single_use=True, condition_eval: str = "True", **attrs):
        
        """初始化一个任务。
        
        Keyword Arguments:
            single_use -- 该任务是否只执行一次。 (default: {True})
        
        Example:
            ```python
            eg_task = CharacterTask(True, strength=100)

            eg_task.add_func(eg_func1, *args, **kwargs)
            eg_task.add_func(eg_func2, *args, **kwargs)
            ```
        """            

        self.attrs_pattern = attrs

        self.single_use = single_use
        self.condition_eval = condition_eval
        self.func_list: list[tuple[str, partial]] = []
        self.func_return = {}

    def add_func(self, func, *args, **kwargs):
        """调用该方法，给任务绑定一个函数。若函数有返回值，则返回值储存在对象的`func_return`属性中。
        
        `func_return`是一个键为函数名，值为函数返回值的字典。
        在子线程中运行的函数无法取得返回值。

        Arguments:
            func -- 一个函数。

        不定参数为函数参数。
        """            

        self.func_list.append((func.__name__, partial(func, *args, **kwargs)))

        self.func_return.update(
            {
                func.__name__: None
            }
        )


class AdvancedCharacter(ADVCharacter): # type: ignore
    """该类继承自ADVCharacter类，在原有的基础上增添了一些新的属性和方法。"""

    def __init__(self, name=None, kind=None, **properties):
        """初始化方法。若实例属性需要被存档保存，则定义对象时请使用`default`语句或Python语句。

        Keyword Arguments:
            name -- 角色名。 (default: {NotSet})
            kind -- 角色类型。 (default: {None})
        """

        if not name:
            name = renpy.character.NotSet # type: ignore

        self.task_list: list[CharacterTask] = []
        self.customized_attr_dict = {}
        super().__init__(name=name, kind=kind, **properties)

    def _emphasize(self, emphasize_callback, t, l):
        """使角色对象支持强调。"""

        if self.image_tag:
            self.display_args["callback"] = partial(emphasize_callback, self, t=t, l=l)
        else:
            raise CharacterError(3)

    def add_task(self, task: CharacterTask):
        """调用该方法，绑定一个角色任务。

        Arguments:
            task -- 一个角色任务。
        """            

        self.task_list.append(task)

    def add_attr(self, **attrs):
        """调用该方法，给该角色对象创建自定义的一系列属性。

        属性可以无初始值。

        Example:
            character.add_attr(strength=100, health=100)     
        """

        for a, v in attrs.items():
            self.set_attr(a, v)

    def set_attr(self, attr, value):
        """调用该方法，修改一个自定义属性的值。若没有该属性则创建一个。

        Arguments:
            attr -- 自定义属性名。
            value -- 要赋予的值。
        """

        setattr(self, attr, value)
        self.customized_attr_dict[attr] = value

    def _check_task(self, attr, value):
        """该方法用于在更新自定义属性值时触发任务。"""

        for task in self.task_list:

            for attr, value in task.attrs_pattern.items():
                if getattr(self, attr) != value or (not eval(task.condition_eval)):
                    break
                    
            else:
                for i in task.func_list:
                    name, func = i
                    func_return = func()
                
                    if func_return:
                        task.func_return[name] = func_return

                if task.single_use:
                    self.task_list.remove(task)

    def __setattr__(self, attr, value):
        """该方法用于在设置自定义属性值时触发任务。"""

        super().__setattr__(attr, value)
        self._check_task(attr, value)

    def get_customized_attr(self):
        """调用该方法，返回一个键为自定义属性，值为属性值的字典，若无则为空字典。

        Returns:
            一个键为自定义属性，值为属性值的字典。
        """

        return self.customized_attr_dict


class CharacterGroup(object):
    """该类用于管理多个高级角色（AdvancedCharacter）对象。"""

    def __init__(self, *characters: AdvancedCharacter):
        """初始化方法。"""

        self.character_group: set[AdvancedCharacter] = set()
        self.add_characters(*characters)

    @staticmethod
    def  _type_check(obj):
        """检查对象类型。"""        

        if isinstance(obj, AdvancedCharacter):
            return
        elif (not isinstance(obj, AdvancedCharacter)) and (isinstance(obj, ADVCharacter)): # type: ignore
            raise CharacterError(0)
        else:
            raise CharacterError(1)

    def add_characters(self, *characters: AdvancedCharacter):
        """调用该方法，向角色组中添加一个或多个角色对象。"""

        for character in characters:
            CharacterGroup._type_check(character)
            self.character_group.add(character)
         
    def get_random_character(self, rp=True):
        """调用该方法，返回角色组中随机一个角色对象。

        Keyword Arguments:
            rp -- 是否使用`renpy`随机数接口。 (default: {True})
        """        

        choice = renpy.random.choice if rp else random.choice # type: ignore
        
        return choice(list(self.character_group))

    def del_characters(self, *characters: AdvancedCharacter):
        """调用该方法，删除角色组中的一个或多个角色。"""
        
        for character in characters:
            CharacterGroup._type_check(character)
            self.character_group.remove(character)

    def add_group_attr(self, **kwargs):
        """调用该方法，对角色组中所有角色对象创建自定义的一系列属性。

        Example:
            character_group.add_group_attr(strength=100, health=100)
        """

        for character in self.character_group:
            character.add_attr(**kwargs)

    def set_group_attr(self, attr, value):
        """调用该方法，更改角色组中所有角色对象的一项自定义属性值。若没有该属性，则创建一个。

        Arguments:
            attr -- 自定义属性名。
            value -- 自定义属性值。
        """

        for character in self.character_group:
            character.set_attr(attr, value)
    
    def set_group_func(self, task: CharacterTask):
        """调用该方法，给所有角色组中的角色对象绑定一个任务。

        Arguments:
            task -- 一个任务。
        """

        for character in self.character_group:
            character.add_task(task)


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
            CharacterGroup._type_check(character)
            character._emphasize(self.emphasize, self.t, self.l)    # 使角色支持强调
            self.character_group.add(character)

    def emphasize(self, character: AdvancedCharacter, event, t=0.15, l=-0.3, **kwargs):
        """该方法用于定义角色对象时作为回调函数使用。该方法可创建一个对话组，对话组中一个角色说话时，其他角色将变暗。
        """            

        if (not event == "begin") or (not self.started):
            return

        if character not in self.character_group:
            self.add_characters(character)
        
        image = renpy.get_say_image_tag() # type: ignore
        if renpy.showing(character.image_tag): # type: ignore
            renpy.show( # type: ignore
                image, 
                at_list=[emphasize(t, 0)] # type: ignore
            )
        
        for speaker in self.character_group:
            if speaker != character and renpy.showing(speaker.image_tag): # type: ignore
                renpy.show( # type: ignore
                    speaker.image_tag, 
                    at_list=[emphasize(t, l)] # type: ignore
                )