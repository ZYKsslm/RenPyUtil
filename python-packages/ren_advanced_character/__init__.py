# 描述  ren_advanced_character 是一个Ren'Py原有角色的扩展，用于轻松创建 RPG 和养成类游戏
# 作者  ZYKsslm
# 仓库  https://github.com/ZYKsslm/RenPyUtil
# 声明  该源码使用 MIT 协议开源，但若使用需要在程序中标明作者信息


try:
    from renpy.exports import version_tuple # type: ignore
except ImportError:
    raise ImportError("ren_advanced_character 要求在 Ren'Py 环境中运行！")

from .character import *
from .task import *
from .exception import *


__version__ = "0.2.0"

__all__ = [
    "AdvancedCharacter",
    "CharacterGroup",
    "SpeakingGroup",
    "CharacterError",
    "CharacterTask",
]


if not (version_tuple.major >= 8 and version_tuple.minor >= 4):
    raise ImportError("ren_advanced_character 要求 Ren'Py 版本 8.4 或以上！")