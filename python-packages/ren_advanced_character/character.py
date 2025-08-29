# 描述  角色相关类
# 作者  ZYKsslm
# 仓库  https://github.com/ZYKsslm/RenPyUtil
# 声明  该源码使用 MIT 协议开源，但若使用需要在程序中标明作者信息


import random

from typing import override
from functools import partial

from .task import CharacterTask
from .exception import ChrErrorType, CharacterError

import renpy.exports as renpy # type: ignore
import renpy.config as config  # type: ignore

from renpy.character import ADVCharacter # type: ignore


class AdvancedCharacter(ADVCharacter):
    """该类继承自ADVCharacter类，在原有的基础上增添了一些新的属性和方法。"""

    def __init__(self, name=None, kind=None, **properties):
        """初始化方法。若实例属性需要被存档保存，则定义对象时请使用`default`语句或Python语句。

        参数与 `Character` 函数一致。
        """

        name = name or renpy.character.NotSet

        self.task_list: list[CharacterTask] = []
        self.user_attrs = set()
        super().__init__(name=name, kind=kind, **properties)

    def _emphasize(self, emphasize_callback, t, l):
        """使角色对象支持强调。"""

        if self.image_tag:
            self.display_args["callback"] = partial(emphasize_callback, self, t=t, l=l)
        else:
            raise CharacterError(ChrErrorType.imageTagError, self.name)

    def add_task(self, task: CharacterTask):
        """调用该方法，绑定一个角色任务。"""   

        if not task.required_attrs.issubset(self.user_attrs):
            raise CharacterError(ChrErrorType.userAttrError)

        self.task_list.append(task)
        if self._check_task not in config.python_callbacks:
            config.python_callbacks.append(self._check_task)

    def set(self, **attrs):
        """调用该方法，给该角色对象创建自定义的一系列属性。"""

        for a, v in attrs.items():
            self.user_attrs.update({a: v})
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

            satisfied_task.append(task)

        for task in satisfied_task:
            for task_func in task.func_list:
                task_func()

            if task.single_use:
                self.task_list.remove(task)


GROUP_INIT_FIELD = ("character_group", "task_list", "t", "l", "started")


class CharacterGroup:
    """该类用于管理多个高级角色对象。"""

    def __init__(self, *characters: AdvancedCharacter):
        self.character_group: list[AdvancedCharacter] = []
        self.add_characters(*characters)
        self.task_list: list[CharacterTask] = []

    @staticmethod
    def  _check_type(obj):
        """检查对象类型。"""        

        if isinstance(obj, AdvancedCharacter):
            return
        raise CharacterError(ChrErrorType.typeError, type(obj).__name__)

    def add_characters(self, *characters: AdvancedCharacter):
        """调用该方法，向角色组中添加一个或多个角色对象。"""

        for character in characters:
            CharacterGroup._check_type(character)
            self.character_group.append(character)
         
    def get_random_character(self, rp=True):
        """调用该方法，返回角色组中随机一个角色对象。

        Args:
            rp: 是否使用`renpy`随机数接口。
        """        

        choice = renpy.random.choice if rp else random.choice
        
        return choice(list(self.character_group))

    def del_characters(self, *characters: AdvancedCharacter):
        """调用该方法，删除角色组中的一个或多个角色。"""
        
        for character in characters:
            CharacterGroup._check_type(character)
            self.character_group.remove(character)

    def set(self, **kwargs):
        """调用该方法，对角色组中所有角色对象创建自定义的一系列属性。

        Args:
            kwargs: 自定义属性及其值。

        Examples:
            ```
            character_group.set(strength=100, health=100)
            ```
            等价于
            ```
            character_group.strength = 100
            character_group.health = 100
            ```
        """

        for character in self.character_group:
            character.set(**kwargs)

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
            
            satisfied_task.append(task)

        for task in satisfied_task:
            for task_func in task.func_list:
                task_func()

            if task.single_use:
                self.task_list.remove(task)

    def __getattr__(self, name):
        if name in GROUP_INIT_FIELD:
            return super().__getattribute__(name)
        else:
            return (getattr(character, name) for character in self.character_group if name in character.user_attrs)
    
    def __setattr__(self, name, value):
        if name in GROUP_INIT_FIELD:
            super().__setattr__(name, value)
        else:
            self.set(**{name: value})


class SpeakingGroup(CharacterGroup):
    """该类继承自CharacterGroup类，用于管理角色发言组。"""

    @override
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

    @override
    def add_characters(self, *characters: AdvancedCharacter):
        for character in characters:
            CharacterGroup._check_type(character)
            character._emphasize(self.emphasize, self.t, self.l)    # 使角色支持强调
            self.character_group.append(character)

    @override
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
        try:
            from renpy.store import emphasize # type: ignore
        except ImportError:
            raise Exception("SpeakingGroup 需要 `speaking_group.rpy` 依赖，请确保依赖文件已存在于 `game/libs` 目录！")

        if renpy.showing(character.image_tag):
            renpy.show(
                image, 
                at_list=[emphasize(t, 0)]
            )
        
        for speaker in self.character_group:
            if speaker != character and renpy.showing(speaker.image_tag):
                renpy.show(
                    speaker.image_tag, 
                    at_list=[emphasize(t, l)]
                )
