# 描述  WebSocket 服务器实现
# 作者  ZYKsslm
# 仓库  https://github.com/ZYKsslm/RenPyUtil
# 声明  该源码使用 MIT 协议开源，但若使用需要在程序中标明作者消息


import uuid
import asyncio
import websockets

from typing import Callable
from websockets.legacy.server import WebSocketServerProtocol

from .logger import get_logger
from .message import Message, MessageCache
from .util import Conductor, IN_RENPY

try:
    import renpy.exports as renpy  # type: ignore
    import renpy.config as config  # type: ignore
except ImportError:
    pass


logger = get_logger("RenServer")

ConnCallback = Callable[[str, WebSocketServerProtocol], None]
DisconnCallback = Callable[[str, WebSocketServerProtocol], None]
RecvCallback = Callable[[str, WebSocketServerProtocol, Message | str | bytes], None]


class RenServer:
    def __init__(self, ip: str = "", port: int = 8888, cache: MessageCache | None = None, **server_kwargs):
        """初始化 WebSocket 服务器。

        :param ip: 监听地址，默认为本机所有地址
        :param port: 监听端口
        :param cache: 消息缓存策略
        :param server_kwargs: 其他参数，参考 `websockets.serve()` 方法
        """

        self.ip = ip
        self.port = port
        self.cache = cache
        self.server_kwargs = server_kwargs

        self.clients: dict[str, WebSocketServerProtocol] = {}
        self.server = None

        self._loop: asyncio.AbstractEventLoop | None = None
        self._conn_callbacks: list[ConnCallback] = []
        self._disconn_callbacks: list[DisconnCallback] = []
        self._recv_callbacks: list[RecvCallback] = []

    async def _client_handler(self, ws: WebSocketServerProtocol):
        if not self._loop:
            return
        
        client_id = str(uuid.uuid4())
        self.clients[client_id] = ws
        logger.info(f"客户端 {client_id} 已连接")
        [
            await Conductor.async_run(cb, client_id, ws) 
            for cb in self._conn_callbacks
        ]
        try:
            async for raw in ws:
                if (msg := Message.parse(raw, self.cache) if isinstance(raw, bytes) else raw):
                    logger.info(f"收到客户端 {client_id} 的消息: {msg}")
                    [
                        await Conductor.async_run(cb, client_id, ws, msg) 
                        for cb in self._recv_callbacks
                    ]
        except Exception as e:
            logger.error(f"客户端 {client_id} 连接异常: {e}")
        finally:
            self.clients.pop(client_id, None)
            logger.info(f"客户端 {client_id} 已断开")
            [
                await Conductor.async_run(cb, client_id, ws) 
                for cb in self._disconn_callbacks
            ]

    def run(self):
        if IN_RENPY and renpy.is_skipping(): # type: ignore
            return
        
        async def _start():
            try:
                self.server = await websockets.serve(
                    self._client_handler, # type: ignore
                    self.ip, 
                    self.port,
                    logger=logger,
                    **self.server_kwargs
                )
                self._loop = self.server.get_loop()
                logger.info(f"服务器已启动")
                await self.server.wait_closed()
            except Exception as e:
                logger.error(f"服务器启动失败: {e}")

        Conductor.invoke_in_thread(asyncio.run, _start())

    def close(self):
        if not self.server or not self._loop:
            return
        try:
            for ws in list(self.clients.values()):
                asyncio.run_coroutine_threadsafe(ws.close(), self._loop)
            self._loop.call_soon_threadsafe(self.server.close)
            logger.info("服务器已关闭")
        except Exception as e:
            logger.warning(f"关闭服务器时发生异常: {e}")
        finally:
            self.clients.clear()
            self._loop = None
            self.server = None

    def reboot(self):
        self.close()
        self.run()

    def _get_client(self, client_id: str, msg: Message | str | bytes):
        ws = self.clients.get(client_id)
        if not ws or ws.closed:
            logger.warning(f"无法发送消息，客户端 {client_id} 不存在或已断开连接")
            return

        if isinstance(msg, Message):
            msg = msg.to_bytes()

        logger.info(f"发送消息 {msg} -> {client_id}")

        return ws, msg

    def send(self, client_id: str, msg: Message | str | bytes):
        if not self._loop:
            return
        
        if (info := self._get_client(client_id, msg)):
            ws, msg = info
            asyncio.run_coroutine_threadsafe(ws.send(msg), self._loop)
        
    async def async_send(self, client_id: str, msg: Message | str | bytes):
        if not self._loop:
            return
        
        if (info := self._get_client(client_id, msg)):
            ws, msg = info
            await ws.send(msg)

    def broadcast(self, msg: Message | str | bytes):
        if not self._loop:
            return

        if isinstance(msg, Message):
            msg = msg.to_bytes()

        async def _broadcast():
            tasks = [ws.send(msg) for ws in self.clients.values() if not ws.closed]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                logger.info(f"广播消息到 {len(tasks)} 个客户端")

        self._loop.call_soon_threadsafe(lambda: asyncio.create_task(_broadcast()))

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
