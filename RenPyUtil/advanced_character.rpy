# 此文件提供了一系列基于Ren'Py的高级角色类
# 仓库  https://github.com/ZYKsslm/RenPyUtil
# 声明  该源码使用 MIT 协议开源，但若使用需要在程序中标明


init python:

    class AdvancedCharacter(ADVCharacter):
        """该类继承自ADVCharacter类，在原有的基础上增添了一些新的属性和方法。"""

        NotSet = renpy.object.Sentinel("NotSet")

        def __init__(self, name=NotSet, kind=None, **properties):
            """初始化方法。若实例属性需要被存档保存，则定义对象时请使用`default`语句或Python语句。

            Keyword Arguments:
                name -- 角色名。 (default: {NotSet})
                kind -- 角色类型。 (default: {None})
            """

            self.func_task_list = []
            self.task_return_dict = {}
            self.customized_attr_list = []
            super().__init__(name, kind=kind, **properties)

        def add_attr(self, attr_dict: dict = None, **attrs):
            """调用此方法，给该角色对象创建自定义的一系列属性。

            Keyword Arguments:
                attr_dict -- 一个键为属性名，值为属性值的字典。若该参数不填，则传入参数作为属性名，参数值作为属性值。 (default: {None})

            Example:
                character.add_attr(strength=100, health=100)
                character.add_attr(attr_dict={strength: 10, health: 5})
            """

            attr = attr_dict if attr_dict else attrs

            for a, v in attr.items():
                self.customized_attr_list.append(a)
                setattr(self, a, v)

        def set_task(self, task_name, attr_pattern: dict, func_dict: dict[function: dict]):
            """调用该函数，创建一个任务，将一个函数与一个或多个自定义属性绑定，当自定义属性变成指定值时执行绑定函数。
            若函数被执行，则函数的返回值储存在实例属性`self.task_return_dict`中。其中键为任务名，值为一个返回值列表。

            Arguments:
                task_name -- 任务名。
                attr_pattern -- 一个键为自定义属性的字典。当该角色对象的自定义属性变成字典中指定的值时执行绑定函数。
                func_dict -- 一个键为函数，值为一个参数字典的字典。
            """
            self.func_task_list.append([task_name, attr_pattern, func_dict])

        def set_attr(self, attr, value):
            """调用该方法，修改一个自定义属性的值。若没有该属性则创建一个。

            Arguments:
                attr -- 自定义属性名。
                value -- 要赋予的值。
            """

            setattr(self, attr, value)

        def __setattr__(self, key, value):
            super().__setattr__(key, value)

            for task in self.func_task_list:
                task_name = task[0]
                attr_dict = task[1]
                func_dict = task[2]

                for attr, value in attr_dict.items():
                    if getattr(self, attr) != value:
                        return
                
                func_return_list = []
                for func, args in func_dict.items():
                    func_return = func(args)
                    func_return_list.append(func_return)

                self.task_return_dict.update(
                    {task_name: func_return_list}
                )
    
        def get_customized_attr(self):
            """调用此方法，返回一个元素为自定义属性的列表，若无则为空列表。

            Returns:
                一个元素为自定义属性的列表。
            """

            return self.customized_attr_list


    class CharacterGroup(object):
        """该类用于管理多个高级角色（AdvancedCharacter）对象。"""

        def __init__(self, character_group: list[AdvancedCharacter] = None, *characters: AdvancedCharacter):
            """初始化方法。

            Keyword Arguments:
                character_group -- 一个包含高级角色对象的元组。若该参数不填，则传入参数作为角色对象。 (default: {None})
            """

            self.character_group = character_group if character_group else list(characters)

        def del_character(self, character):
            """调用该函数，删除角色组中的一个角色对象。

            Arguments:
                character -- 要删除的角色对象。
            """

            self.character_group.remove(character)

        def add_group_attr(self, attr_dict: dict = None, **attrs):
            """调用该函数，对角色组中所有角色对象创建自定义的一系列属性。

            Keyword Arguments:
                attr_dict -- 一个键为属性名，值为属性值的字典。若该参数不填，则传入参数作为属性名，参数值作为属性值。 (default: {None})

            Example:
                character_group.add_group_attr(strength=100, health=100)
                character_group.add_group_attr(attr_dict={strength: 10, health: 5})
            """

            attr = attr_dict if attr_dict else attrs

            for character in self.character_group:
                character.add_attr(attr_dicr=attr)

        def set_group_attr(self, attr, value):
            """调用该函数，更改角色组中所有角色对象的一项自定义属性值。若没有该属性，则创建一个。

            Arguments:
                attr -- 自定义属性名。
                value -- 自定义属性值。
            """

            for character in self.character_group:
                character.set_attr(attr, value)
        
        def set_group_func(self, task_name, attr_pattern: dict, func_dict: dict[function: dict]):
            """调用该函数，给所有角色组中的角色对象创建一个任务，将一个函数与一个或多个自定义属性绑定，当自定义属性变成指定值时执行绑定函数。
            若函数被执行，则函数的返回值储存在对象的实例属性`self.task_return_dict`中。其中键为任务名，值为一个返回值列表。

            Arguments:
                task_name -- 任务名。
                attr_pattern -- 一个键为自定义属性的字典。当该角色对象的自定义属性变成字典中指定的值时执行绑定函数。
                func_dict -- 一个键为函数，值为一个参数字典的字典。
            """

            for character in self.character_group:
                character.set_task(task_name, attr_pattern, func_dict)