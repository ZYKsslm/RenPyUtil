from enum import Enum


class ChrErrorType(Enum):
    typeError = "对象类型错误，应为AdvancedCharacter而非 `{}`！"
    imageTagError = "图像标签错误，请检查角色 `{}` 是否绑定了图像标签！"
    handlerError = "handler参数 必须为 `jump` 或 `call`，而非 `{}`！"
    userAttrError = "要绑定的人物中使用了不存在的角色属性！"


class CharacterError(Exception):
    """该类为一个异常类，用于检测角色对象有关的错误。"""


    def __init__(self, error_type: ChrErrorType, *args):
        super().__init__()
        self.error_type = error_type
        self.args = args

    def __str__(self):
        return self.error_type.value.format(*self.args)
    