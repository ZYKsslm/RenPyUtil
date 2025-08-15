# 描述  WebSocket 客户端实现
# 作者  ZYKsslm
# 仓库  https://github.com/ZYKsslm/RenPyUtil
# 声明  该源码使用 MIT 协议开源，但若使用需要在程序中标明作者消息


import threading
import websockets

from typing import Callable
from websockets.sync.client import connect
from websockets.sync.client import ClientConnection

from .logger import get_logger
from .message import Message, MessageCache
from .util import Conductor, FakeBlock, IN_RENPY

try:
    import renpy.exports as renpy  # type: ignore
    import renpy.config as config  # type: ignore
except ImportError:
    pass

logger = get_logger("RenClient")

ConnCallback = Callable[[], None]
DisconnCallback = Callable[[], None]
RecvCallback = Callable[[Message | str | bytes], None]


class RenClient:

    def __init__(self, 
        target_ip: str, 
        target_port: int, 
        cache: MessageCache | None = None, 
        **connect_kwargs
    ):
        """初始化 Websockets 客户端。

        :param target_ip: 目标服务器 IP 地址
        :param target_port: 目标服务器端口
        :param cache: 缓存策略
        :param connect_kwargs: 连接参数，参考 `websockets.connect()` 方法
        """

        self.target_ip = target_ip
        self.target_port = target_port
        self.target_uri = f"ws://{target_ip}:{target_port}"
        self.connect_kwargs = connect_kwargs
        self.cache = cache

        self.websocket: ClientConnection | None = None
        self._thread: threading.Thread | None = None
        self._max_retries = 5
        self.stop_event = threading.Event()

        self._conn_callbacks: list[ConnCallback] = []
        self._disconn_callbacks: list[DisconnCallback] = []
        self._recv_callbacks: list[RecvCallback] = []

    def _handler(self, websocket: ClientConnection):
        while not self.stop_event.is_set():
            try:
                raw = websocket.recv()
                if (msg := Message.parse(raw, self.cache) if isinstance(raw, bytes) else raw):
                    logger.info(f"收到服务器的消息: {msg}")
                    for cb in self._recv_callbacks:
                        try:
                            cb(msg)
                        except Exception as e:
                            logger.warning(f"执行接收回调 {cb.__name__} 时发生异常: {e}")

            except websockets.ConnectionClosed as e:
                logger.warning(f"断开连接: {e}")

                for cb in self._disconn_callbacks:
                    try:
                        cb()
                    except Exception as e:
                        logger.warning(f"执行断连回调 {cb.__name__} 时发生异常: {e}")

                self.websocket = None
                self._thread = None
                self.stop_event.clear()
                return

            except Exception as e:
                logger.warning(f"接收消息时发生异常: {e}")

    def _connect(self):
        retry_count = 1
        while (not self.stop_event.is_set()) and retry_count < self._max_retries:
            try:
                logger.info(f"第 {retry_count} 次尝试连接到服务器 {self.target_uri}")
                with connect(self.target_uri, logger=logger, open_timeout=2, **self.connect_kwargs) as websocket:  
                    self.websocket = websocket # type: ignore
                    logger.info("已连接服务器")
                    for cb in self._conn_callbacks:
                        try:
                            cb()
                        except Exception as e:
                            logger.warning(f"执行连接回调 {cb.__name__} 时发生异常: {e}")
                        
                    self._handler(websocket) # type: ignore

            except Exception as e:
                retry_count += 1
                delay = min(2 ** retry_count, 60)
                logger.warning(f"连接失败: {e} {delay}秒后重试")
                self.stop_event.wait(delay)

        logger.warning("停止连接")

    def send(self, msg: Message | str | bytes, block: bool = True):
        """发送消息。

        :param msg: 消息内容
        :param block: 是否伪阻塞等待发送
        """

        if not self.websocket or self.stop_event.is_set():
            return
        
        if isinstance(msg, Message):
            msg = msg.to_bytes()

        if block and IN_RENPY:
            FakeBlock(self.websocket.send, msg).start()
        else:
            Conductor.invoke_in_thread(self.websocket.send, msg)

    def run(self):
        if IN_RENPY and renpy.is_skipping(): # type: ignore
            return

        if self._thread and self._thread.is_alive():
            raise RuntimeError("该客户端已在运行")

        self.stop_event.clear()
        self._thread = threading.Thread(target=self._connect, daemon=True)
        self._thread.start()

    def close(self):
        try:
            self.stop_event.set()
            if self.websocket:
                self.websocket.close()
            if self._thread and self._thread.is_alive():
                if IN_RENPY:
                    FakeBlock(self._thread.join).start()
                else:
                    self._thread.join()
            logger.info("连接已关闭")
        except Exception as e:
            logger.warning(f"关闭连接时发生异常：{e}")
        finally:
            self.websocket = None
            self._thread = None

    def reboot(self):
        self.close()
        self.run()

    def on_conn(self, cb: ConnCallback):
        self._conn_callbacks.append(cb)
        return cb

    def on_disconn(self, cb: DisconnCallback):
        self._disconn_callbacks.append(cb)
        return cb

    def on_recv(self, cb: RecvCallback):
        self._recv_callbacks.append(cb)
        return cb
    
    def __enter__(self):
        if IN_RENPY:
            config.rollback_enabled = False # type: ignore
            renpy.block_rollback() # type: ignore
        self.run()
        logger.info("进入上下文管理器，回滚功能已暂时禁用")  
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if IN_RENPY:
            config.rollback_enabled = True # type: ignore
            renpy.block_rollback() # type: ignore
        self.close()
        logger.info("退出上下文管理器，回滚功能已恢复")
