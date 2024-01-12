# 此文件提供了一系列基于Ren'Py的功能类，以供Ren'Py开发者调用
# 作者  ZYKsslm
# 仓库  https://github.com/ZYKsslm/RenPyUtil
# 声明  该源码使用 MIT 协议开源，但若使用需要在程序中标明作者信息


# 对话组使用的transform
"""renpy
transform off_stress():
    linear 0.15 alpha 0.5

transform stress():
    linear 0.15 alpha 1.0
"""

"""renpy
init -1 python:
"""

from functools import partial


def threading_task(func):
    """一个装饰器，被装饰的函数将在子线程中运行。

    Arguments:
        func -- 一个函数。
    """        

    def wrapper(*args, **kwargs):
        renpy.invoke_in_thread(func, *args, **kwargs)
    return wrapper


class CharacterTask(object):
    """该类为角色任务类，用于高级角色对象绑定任务。"""        

    def __init__(self, attr_pattern: dict = {}, single_use=True):
        
        """初始化一个任务。

        Keyword Arguments:
            attr_pattern -- 一个键为自定义属性的字典。当该角色对象的自定义属性变成字典中指定的值时执行绑定函数。 (default: {{}})
            single_use -- 若为True，则该任务为一次性任务，即当执行过一次后就移除该任务。 (default: {True})

        Example:
            ```python
            eg_task = CharacterTask(
                attr_pattern={
                    "love": 100,
                    "health": 50
                }
            )

            eg.add_func(eg_func1, arg, kwarg="")
            eg.add_func(eg_func2, arg, kwarg="")
            ```
        """            

        self.attr_pattern = attr_pattern
        self.single_use = single_use
        self.func_dict = {}

        self.func_return = {}
        for fn in self.func_dict.keys():
            self.func_return.update(
                {
                    fn.__name__: None
                }
            )

    def add_func(self, func, *args, **kwargs):
        """调用该方法，给任务绑定一个函数。若函数有返回值，则返回值储存在对象的`func_return`属性中。
        `func_return`是一个键为函数名，值为函数返回值的字典。
        在子线程中运行的函数无法取得返回值。

        Arguments:
            func -- 一个函数。

        不定参数为函数参数。
        """            

        self.func_dict.update(
            {
                func: (args, kwargs)
            }
        )

        self.func_return.update(
            {
                func.__name__: None
            }
        )


class CharacterError(Exception):
    """该类为一个异常类，用于检测角色对象。"""

    errorType = {
        0: "错误地传入了一个ADVCharacter类，请传入一个AdvancedCharacter高级角色类！",
        1: "传入对象类型错误!",
        2: "该角色对象不在角色组内！"
    }

    def __init__(self, errorCode):
        super().__init__()
        self.errorCode = errorCode

    def __str__(self):
        return CharacterError.errorType[self.errorCode]


NotSet = renpy.object.Sentinel("NotSet")
class AdvancedCharacter(ADVCharacter):
    """该类继承自ADVCharacter类，在原有的基础上增添了一些新的属性和方法。"""

    def __init__(self, name=NotSet, kind=None, **properties):
        """初始化方法。若实例属性需要被存档保存，则定义对象时请使用`default`语句或Python语句。

        Keyword Arguments:
            name -- 角色名。 (default: {NotSet})
            kind -- 角色类型。 (default: {None})
        """

        super().__init__(name, kind=kind, **properties)
        self.properties = properties
        self.task_list = []
        self.customized_attr_dict = {}

    def add_attr(self, attr_dict: dict = None, **attrs):
        """调用该方法，给该角色对象创建自定义的一系列属性。

        Keyword Arguments:
            attr_dict -- 一个键为属性名，值为属性值的字典。若该参数不填，则传入参数作为属性名，参数值作为属性值。 (default: {None})

        Example:
            character.add_attr(strength=100, health=100)
            character.add_attr(attr_dict={strength: 10, health: 5})
        """

        attr = attr_dict if attr_dict else attrs

        for a, v in attr.items():
            setattr(self, a, v)
            self.customized_attr_dict[a] = v

    def add_task(self, task: CharacterTask):
        """调用该方法，绑定一个角色任务。

        Arguments:
            task -- 一个角色任务。
        """            

        self.task_list.append(task)

    def set_attr(self, attr, value):
        """调用该方法，修改一个自定义属性的值。若没有该属性则创建一个。

        Arguments:
            attr -- 自定义属性名。
            value -- 要赋予的值。
        """

        setattr(self, attr, value)
        self.customized_attr_dict[attr] = value

    def __setattr__(self, key, value):
        super().__setattr__(key, value)

        # 跳过初始化属性赋值阶段
        # 跳过非自定义属性赋值阶段
        if (not hasattr(self, "customized_attr_dict")) or (not key in self.customized_attr_dict.keys()):
            return

        for task in self.task_list:

            for attr, value in task.attr_pattern.items():
                if getattr(self, attr) != value:
                    break
                    
            else:
                for func, params in task.func_dict.items():
                    args, kwargs = params
                    func_return = func(*args, **kwargs)
                
                    if func_return:
                        task.func_return[func.__name__] = func_return

                if task.single_use:
                    self.task_list.remove(task)

    def get_customized_attr(self):
        """调用该方法，返回一个键为自定义属性，值为属性值的字典，若无则为空字典。

        Returns:
            个键为自定义属性，值为属性值的字典。
        """

        return self.customized_attr_dict


class CharacterGroup(object):
    """该类用于管理多个高级角色（AdvancedCharacter）对象。"""

    def __init__(self, *characters: AdvancedCharacter):
        """初始化方法。"""

        self.speaking_group = []

        self.character_group = list(characters)

        # 检查角色组中对象类型
        for obj in self.character_group:
            if isinstance(obj, AdvancedCharacter):
                pass
            elif (not isinstance(obj, AdvancedCharacter)) and (isinstance(obj, ADVCharacter)):
                raise CharacterError(0)
            else:
                raise CharacterError(1)

    def add_characters(self, *characters: AdvancedCharacter):
        """调用该方法，向角色组和对话组中添加一个或多个角色对象。"""

        for character in characters:
            if isinstance(character, AdvancedCharacter):
                self.character_group.append(character)
            elif (not isinstance(character, AdvancedCharacter)) and (isinstance(character, ADVCharacter)):
                raise CharacterError(0)
            elif isinstance(character, str):
                self.speaking_group.append(character)  
            else:
                raise CharacterError(1)
         
    def get_random_character(self):
        """调用该方法，返回角色组中随机一个角色对象。"""

        character = renpy.random.choice(self.character_group)
        return character
    
    def get_random_speaker(self):
        """调用该方法，返回对话组中随机一个角色对象。"""
        
        speaker = eval(renpy.random.choice(self.speaking_group))
        return speaker

    def del_characters(self, *characters):
        """调用该方法，删除角色组或对话组中的一个或多个角色。

        Arguments:
            character -- 要删除的角色对象。
        """
        
        for character in characters:
            if isinstance(character, AdvancedCharacter):
                self.character_group.remove(character)
            elif isinstance(character, str):
                self.speaking_group.remove(character)
            else:
                raise CharacterError(2)

    def add_group_attr(self, attr_dict: dict = None, **attrs):
        """调用该方法，对角色组中所有角色对象创建自定义的一系列属性。

        Keyword Arguments:
            attr_dict -- 一个键为属性名，值为属性值的字典。若该参数不填，则传入参数作为属性名，参数值作为属性值。 (default: {None})

        Example:
            character_group.add_group_attr(strength=100, health=100)
            character_group.add_group_attr(attr_dict={strength: 10, health: 5})
        """

        attr = attr_dict if attr_dict else attrs

        for character in self.character_group:
            character.add_attr(attr)

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

    def stress(self, name: str, event, close=False, **kwargs):
        """该方法用于定义角色对象时作为回调函数使用。该方法可创建一个对话组，对话组中一个角色说话时，其他角色将变暗。

        Arguments:
            name -- 角色对象的字符串形式。
            event -- 自动传入的事件。
        """            

        if not event == "begin":
            return

        if name not in self.speaking_group:
            self.speaking_group.append(name)
        
        for speaker in self.speaking_group:
            current_name = speaker
            speaker = eval(speaker)
            image = speaker.properties["image"]
            
            if current_name == name:
                renpy.show(image, at_list=[stress])
                continue
            
            renpy.show(image, at_list=[off_stress])