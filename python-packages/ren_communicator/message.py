# 描述  RenCommunicator 是一个轻量化异步 websocket 通信库，用于在 Ren'Py 游戏中实现网络通信，适用于小型网络游戏。
# 作者  ZYKsslm
# 仓库  https://github.com/ZYKsslm/RenPyUtil
# 声明  该源码使用 MIT 协议开源，但若使用需要在程序中标明作者消息


import os 
import shutil
import hashlib
import msgpack

from enum import Enum
from typing import TypedDict
from functools import partial

from .util import IN_RENPY
from .logger import get_logger

try:
    import renpy.exports as renpy # type: ignore
    import renpy.config as config # type: ignore
    import renpy.display.im as im # type: ignore

    from renpy.display.video import Movie # type: ignore
    from renpy.audio.audio import AudioData # type: ignore

    gamedir = config.gamedir

except ImportError:
    
    gamedir = os.getcwd()


logger = get_logger("MessageHandler")


class MessageType(Enum):
    STRING = 0
    JSON = 1
    IMAGE = 2
    AUDIO = 3
    MOVIE = 4


class MessageDict(TypedDict):
    type: int
    data: bytes
    fmt: str | None
    params: dict | None


class MessageCache:
    """制定消息缓存策略。"""

    CACHE_DIR = "media_cache"
    CACHED_SIZE = 0

    def __init__(self, 
        max_size: int = 1024 * 1024 * 1024, 
        msg_min_size: int = 10 * 1024 * 1024,
    ):
        """初始化消息缓存。

        :param max_size: 最大缓存大小，默认为 1GB。
        :param msg_min_size: 当消息小于该值时，不使用缓存，默认为 10MB（但视频会强制缓存）
        """
        
        self.max_size = max_size
        self.msg_min_size = msg_min_size
        self.cached_fils = set(os.listdir(MessageCache.parse_path(MessageCache.CACHE_DIR)))

    @staticmethod
    def parse_path(*renpy_paths):
        """调用该静态方法，把标准 Ren'Py 路径转换为绝对路径。
        
        Returns:
            一个绝对路径。
        """
        
        return os.path.join(gamedir, *renpy_paths)

    @staticmethod
    def clear_cache():
        """清除缓存。"""

        cache_path = MessageCache.parse_path(MessageCache.CACHE_DIR)
        shutil.rmtree(cache_path, ignore_errors=True)
        os.makedirs(cache_path, exist_ok=True)

    def cache(self, msg_info: MessageDict):
        """缓存消息。"""

        cache_path = MessageCache.parse_path(MessageCache.CACHE_DIR)
        size = len(msg_info["data"])

        if (
            msg_info["type"] != MessageType.MOVIE.value and
            ((size < self.msg_min_size) or 
            (size + MessageCache.CACHED_SIZE >= self.max_size))
        ):
            return
        
        if not os.path.exists(cache_path):
            os.mkdir(cache_path)

        cache_name = f'{hashlib.sha256(msg_info["data"]).hexdigest()}{msg_info["fmt"]}'
        if cache_name not in self.cached_fils:
            with open(os.path.join(cache_path, cache_name), "wb") as f:
                f.write(msg_info["data"])

            MessageCache.CACHED_SIZE += size
        
            self.cached_fils.add(cache_name)
        
        return f"{MessageCache.CACHE_DIR}/{cache_name}"
    

class Message:

    def __init__(self, 
        _type: MessageType, 
        data: str | bytes | list | dict | None, 
        fmt: str | None = None, 
        params: dict | None = None, 
        cache_path: str | None = None, 
    ):
        """初始化一个消息。

        :param _type: 消息类型
        :param data: 消息数据
        :param fmt: 媒体消息文件格式
        :param params: 额外参数（可json化字典）
        :param cache_path: 缓存路径
        """

        self.type = _type
        self.data = data
        self.fmt = fmt
        self.params = params
        self.cache_path = cache_path
        
        self._content = None

    @classmethod
    def parse(cls, message: bytes, cache: MessageCache | None = None):
        """从字节串中解析出消息。

        :param message: 原始消息
        :param cache: 缓存策略

        :return: 一个 `Message` 对象
        """

        msg: MessageDict = msgpack.unpackb(message)
        try:
            _type = MessageType(msg["type"])
            data = msg["data"]
            fmt = msg.get("fmt")
            params = msg.get("params")
        except Exception as e:
            logger.warning(f"解析消息失败: {e}")
        else:
            if cache and (cache_path := cache.cache(msg)):
                logger.info(f"解析消息成功: type={_type}, fmt='{fmt}', params={params}, cache_path='{cache_path}'")
                return cls(_type, None, fmt, params, cache_path)
            
            logger.info(f"解析消息成功: type={_type}, fmt='{fmt}', params={params}")
            return cls(_type, data, fmt, params)

    @property
    def content(self):
        if self._content is None:
            self._content = self._get()
            
        return self._content

    def _get(self):
        """获取消息内容
        
        Returns:
            根据消息类型解析出的消息内容
            - `Ren'Py 标准路径`
            - `str`
            - `Displayable`
            - `AudioData`
            - `Movie`
        """

        if self.cache_path:
            return self.cache_path

        match self.type:
            case MessageType.STRING | MessageType.JSON:
                content = self.data
            case MessageType.IMAGE:
                content = self._to_image()
            case MessageType.AUDIO:
                content = self._to_audio()
            case MessageType.MOVIE:
                content = self._to_movie()
            case _:
                content = None

        return content

    def _to_image(self):
        if not IN_RENPY:
            raise RuntimeError("不在 Ren'Py 环境中，无法加载图像")
        
        return im.Data(self.data, self.fmt) # type: ignore

    def _to_audio(self):
        if not IN_RENPY:
            raise RuntimeError("不在 Ren'Py 环境中，无法加载音频")
        
        return AudioData(self.data, self.fmt) # type: ignore
        
    def _to_movie(self):
        if not IN_RENPY:
            raise RuntimeError("不在 Ren'Py 环境中，无法加载视频")
        
        return Movie(play=self.cache_path) # type: ignore

    def to_bytes(self) -> bytes:
        """将消息转换为字节串。用于网络传输。"""

        if self.data is None and self.cache_path:
            data = MessageBuilder._get_data(self.cache_path)
        else:
            data = self.data

        info = {
            "type": self.type.value,
            "data": data,
            "fmt": self.fmt,
            "params": self.params
        }
        return msgpack.packb(info) # type: ignore

    def __repr__(self):
        match self.type:
            case MessageType.STRING | MessageType.JSON:
                return f"Message(type=MessageType.{self.type.name}, data={self.data})"
            case _:
                if self.cache_path:
                    return f"Message(type=MessageType.{self.type.name}, fmt='{self.fmt}', cache_path='{self.cache_path}')"
                else:
                    return f"Message(type=MessageType.{self.type.name}, data=..., fmt='{self.fmt}')"


class MessageBuilder:
    
    @staticmethod
    def _get_data(path: str):
        loadable = renpy.loadable if IN_RENPY else os.path.exists # type: ignore
        open_file = partial(renpy.open_file, encoding=False) if IN_RENPY else partial(open, mode="rb") # type: ignore

        if not loadable(path):
            logger.warning(f"文件不存在: {path}")
            return

        with open_file(path) as f:
            data = f.read()
        
        return data

    @staticmethod
    def from_string(string: str):
        """从字符串创建消息。"""

        return Message(MessageType.STRING, string)

    @staticmethod
    def from_json(json: list | dict):
        """从 JSON 结构对象创建消息。"""

        return Message(MessageType.JSON, json)

    @staticmethod
    def from_media(path: str, _type: MessageType):
        """从媒体文件创建消息。"""

        if (data := MessageBuilder._get_data(path)):
            return Message(_type, data, os.path.splitext(path)[1])

    @staticmethod
    def from_image(path: str):
        """从图像创建消息。"""

        return MessageBuilder.from_media(path, MessageType.IMAGE)

    @staticmethod
    def from_audio(path: str):
        """从音频创建消息。"""

        return MessageBuilder.from_media(path, MessageType.AUDIO)

    @staticmethod
    def from_movie(path: str):
        """从视频创建消息。"""

        return MessageBuilder.from_media(path, MessageType.MOVIE)

