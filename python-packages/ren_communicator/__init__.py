# 描述  RenCommunicator 是一个轻量化异步 websocket 通信库，用于在 Ren'Py 游戏中实现网络通信，适用于小型网络游戏。
# 作者  ZYKsslm
# 仓库  https://github.com/ZYKsslm/RenPyUtil
# 声明  该源码使用 MIT 协议开源，但若使用需要在程序中标明作者消息


from .message import *
from .server import *
from .client import *
from .util import *


__version__ = "0.2.0"

__all__ = [
    "Message", 
    "MessageCache", 
    "MessageType", 
    "MessageDict", 
    "MessageBuilder", 
    "RenServer", 
    "RenClient", 
    "Conductor", 
    "FakeBlock"
]


if IN_RENPY:
    from renpy.exports import version_tuple # type: ignore

    if version_tuple.major < 8:
        raise ImportError("RenCommunicator 要求 Ren'Py 版本 8.0 或以上。")
