# 此文件提供了一系列基于Ren'Py的功能类，以供Ren'Py开发者调用
# 作者  ZYKsslm
# 仓库  https://github.com/ZYKsslm/RenPyUtil
# 声明  该源码使用 MIT 协议开源，但若使用需要在程序中标明作者消息


"""renpy
init -1 python:
"""


import logging
import os 
import pickle
import socket
import time
from typing import Optional


# Ren'Py 相关
renpy = renpy # type: ignore
config = config # type: ignore
preferences = preferences # type: ignore
im = im # type: ignore
AudioData = AudioData # type: ignore
Movie = Movie # type: ignore


def set_logger(logger_name: str, log_path: str):
    """返回一个日志记录器，包含文件输出和标准控制台输出。

    Arguments:
        logger_name -- 日志名称
        log_path -- 日志文件路径
    """

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(os.path.join(config.basedir, log_path), encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(threadName)s - %(message)s")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


class Message(object):
    """消息类，用于创建通信中收发的消息对象"""

    logger = set_logger("Message", "RenCommunicator.log")

    STRING = "string".encode() # 字符串类型
    IMAGE = "image".encode()  # 图片类型
    AUDIO = "audio".encode()  # 音频类型
    MOVIE = "movie".encode()  # 影片类型
    OBJECT = "object".encode()  # 其他 Python 对象类型

    def __init__(self, msg: bytes, data: bytes = None, type: bytes = None, fmt: bytes = None):
        """消息构建方法。一般不显示调用，而是使用类方法创建消息。

        Arguments:
            msg -- 原始消息

        Keyword Arguments:
            data -- 消息数据 (default: {None})
            type -- 消息类型 (default: {None})
            fmt -- 消息格式 (default: {None})
        """

        if not data and not type and not fmt:
            self.type, self.fmt, self.data = msg.split(b"|", 2)
        else:
            self.type = type
            self.fmt = fmt
            self.data = data

        self.msg = msg
        self.log_info = {
            "type": self.type.decode(),
            "size": len(self.data),
            "format": None,
            "message": None,
            "class": None
        }
        if self.type == self.STRING:
            self.log_info["message"] = self.data.decode()
        elif self.type == self.OBJECT:
            self.log_info["class"] = self.fmt.decode()
        else:
            self.log_info["format"] = self.fmt.decode()

        self._message = None
        self._image = None
        self._audio = None
        self._movie = None
        self._object = None

    @staticmethod
    def parse_path(*renpy_paths):
        """调用该静态方法，把标准 Ren'Py 路径转换为绝对路径。
        
        Returns:
            一个绝对路径。
        """
        
        return os.path.join(config.gamedir, *renpy_paths)

    @classmethod
    def string(cls, msg: str):
        """调用该类方法，创建字符串消息。

        Arguments:
            msg -- 字符串消息

        Returns:
            一个 `Message` 对象
        """

        prefix = cls.STRING + b"|" + b"|"
        data = msg.encode()
        msg = prefix + data
        return cls(msg, data, cls.STRING)

    @classmethod
    def image(cls, img_path: str):
        """调用该类方法，创建图片消息。

        Arguments:
            img_path -- 图片路径

        Returns:
            一个 `Message` 对象
 
        """

        if not os.path.exists(img_path):
           Message.logger.warning(f"未找到该图片：{img_path}，请确保路径符合 Ren'Py 规范")
        else:
            with open(img_path, "rb") as img:
                data = img.read()

            fmt = os.path.splitext(img_path)[1].encode()
            prefix = cls.IMAGE + b"|" + fmt + b"|"
            msg = prefix + data
            return cls(msg, data, cls.IMAGE, fmt)

    @classmethod
    def audio(cls, audio_path: str):
        """调用该类方法，创建音频消息。

        Arguments:
            audio_path -- 音频路径

        Returns:
            一个 `Message` 对象
        """

        if not os.path.exists(audio_path):
            Message.logger.warning(f"未找到该音频：{audio_path}，请确保路径符合 Ren'Py 规范")
        else:
            with open(audio_path, "rb") as audio:
                data = audio.read()

            fmt = os.path.splitext(audio_path)[1].encode()
            prefix = cls.AUDIO + b"|" + fmt + b"|"
            msg = prefix + data
            return cls(msg, data, cls.AUDIO, fmt)

    @classmethod
    def movie(cls, movie_path: str):
        """调用该类方法，创建影片消息。

        Arguments:
            movie_path -- 影片路径

        Returns:
            一个 `Message` 对象

        Raises:
            Exception -- 若影片路径不存在，则抛出异常。 
        """

        if not os.path.exists(movie_path):
            Message.logger.warning(f"未找到该影片：{movie_path}，请确保路径符合 Ren'Py 规范")
        else:
            with open(movie_path, "rb") as movie:
                data = movie.read()

            fmt = os.path.splitext(movie_path)[1].encode()
            prefix = cls.MOVIE + b"|" + fmt + b"|"
            msg = prefix + data
            return cls(msg, data, cls.MOVIE, fmt)
        
    @classmethod
    def object(cls, obj: object):
        """调用该类方法，创建其他 Python 对象消息。

        Arguments:
            obj -- 其他 Python 对象

        Returns:
            一个 `Message` 对象 
        """

        try:
            data = pickle.dumps(obj)
        except pickle.PicklingError:
            Message.logger.warning(f"无法序列化 {obj} 对象")
        else:
            fmt = type(obj).__name__.encode()
            prefix = cls.OBJECT + b"|" + fmt + b"|"
            msg = prefix + data
            return cls(msg, data, cls.OBJECT, fmt)

    def get_message(self):
        """若消息类型为字符串，则返回该字符串。否则返回 None"""

        if self.type != self.STRING:
            return
        
        if not self._message:
            self._message = self.data.decode()
            Message.logger.debug(f"成功解析字符串消息：{self._message}")

        return self.data.decode()

    def get_image(self):
        """若消息类型为图片，则返回该图片的可视组件。否则返回 None"""

        if self.type != self.IMAGE:
            return
        
        if not self._image:
            self._image = im.Data(self.data, self.fmt.decode())
            Message.logger.debug(f"成功将图片解析为可视组件：{self._image}")

        return self._image

    def get_audio(self):
        """若消息类型为音频，则返回一个音频对象，该对象可直接使用 `play` 语句播放。否则返回 None"""

        if self.type != self.AUDIO:
            return
        
        if not self._audio:
            self._audio = AudioData(self.data, self.fmt.decode())
            Message.logger.debug(f"成功将音频解析为音频对象：{self._audio}")

        return self._audio
        
    def get_movie(self, cache_path: str = "movie_cache", **kwargs):
        """_summary_

        Keyword Arguments:
            cache_path -- 视频缓存目录 (default: {None})

        Returns:
            一个 `Movie` 可视组件

        其他关键字参数将传递给 `Movie` 类
        """

        if self.type != self.MOVIE:
            return
        
        if not self._movie:
            cache_name = f"{int(time.time())}{self.fmt.decode()}"
            cache_dir = Message.parse_path(cache_path)
            cache_path = Message.parse_path(cache_path, cache_name)
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)

            with open(cache_path, "wb") as cache:
                cache.write(self.data)
            Message.logger.debug(f"成功将影片缓存到 {cache_path}")

            self._movie = Movie(play=cache_path, **kwargs)
            Message.logger.debug(f"成功将影片解析为可视组件：{self._movie}")

        return self._movie

    def get_object(self):
        """若消息类型为其他 Python 对象，则返回该对象。否则返回 None"""

        if self.type != self.OBJECT:
            return
        
        if not self._object:
            try:
                self._object = pickle.loads(self.data)
            except pickle.UnpicklingError:
                RenServer.logger.warning(f"无法解析 {self.fmt.decode()} 对象")
                return

        return self._object


class RenServer(object):
    """该类为一个服务器类。基于socket进行多线程通信"""

    logger = set_logger("RenServer", "RenCommunicator.log")
    
    def __init__(self, max_conn=5, max_data_size=104857600, ip="0.0.0.0", port=8888):
        """初始化方法。

        Keyword Arguments:
            max_conn -- 最大连接数。 (default: {5})
            max_data_size -- 接收数据的最大大小。默认为100M。 (default: {104857600})
            port -- 端口号。 (default: {None})
        """            

        self.port = port
        self.ip = ip
        self.max_data_size = max_data_size
        self.max_conn = max_conn
        self.socket = None

        self.client_socket_dict: dict[str, socket.socket] = {}
        self.conn_event = []
        self.disconn_event = []
        self.recv_event = []

        self.chat_mode = False
        self.chat_screen = "ren_communicator_chat"
        self.msg_list: list[tuple[socket.socket, Message]] = []
        
    def run(self):
        """调用该方法，开始监听端口，创建连接线程。在快进状态下不会有任何效果"""   

        if renpy.is_skipping():
            return         
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((self.ip, self.port))
        except OSError:
            RenServer.logger.error(f"端口 {self.port} 已被占用，请检查是否有其他进程占用或是打开了多个游戏")
        else:
            self.socket.listen(self.max_conn)
            RenServer.logger.info(f"服务器已启动，开始监听端口：{self.port}")
            renpy.invoke_in_thread(self._accept)
    
    def close(self):
        """调用该方法，关闭服务器"""

        for client_socket in self.client_socket_dict.values():
            client_socket.close()
        self.client_socket_dict.clear()
        self.socket.close() 

    def reboot(self):
        """调用该方法，重启服务器"""

        self.close()
        self.run()
    
    def _accept(self):
        """该方法用于创建连接线程，用于类内部使用，不应被调用"""            

        while True:
            try:
                client_socket = self.socket.accept()[0]
            except OSError:
                RenServer.logger.warning("服务器已关闭")
                break
            else:
                client_name = f"{client_socket.getpeername()[0]}:{client_socket.getpeername()[1]}"
                RenServer.logger.info(f"{client_name} 已连接")
                if self.chat_mode:
                    renpy.show_screen(self.chat_screen, self, True, client_socket)
                self.client_socket_dict[client_name] = client_socket
                renpy.invoke_in_thread(self._receive, client_name, client_socket)
                for event in self.conn_event:
                    event(self, client_name, client_socket)

    def _receive(self, client_name, client_socket):
        """该方法用于接收线程使用，处理接收事件，用于类内部使用，不应被调用"""

        while True:
            try:
                data = client_socket.recv(self.max_data_size)
            except ConnectionError:
                RenServer.logger.warning(f"{client_name} 已断开连接")
                if client_name in self.client_socket_dict.keys():
                    del self.client_socket_dict[client_name]
                for event in self.disconn_event:
                    event(self, client_name)
                break
            else:
                msg = Message(data)
                if self.chat_mode:
                    self.msg_list.append((client_socket, msg))
                RenServer.logger.debug(f"接收到 {client_name} 的消息：{msg.log_info}")
                for event in self.recv_event:
                    event(self, client_name, client_socket, msg)

    def send(self, client_socket: socket.socket, msg: Message, block=False):
        """调用该方法，向指定客户端发送消息。

        Arguments:
            client_socket -- 客户端socket。
            msg -- 要发送的消息。

        Keyword Arguments:
            block -- 若为True，则该方法将阻塞，直到发送完成。 (default: {False})
        """            
        
        if block:
            self._send(client_socket, msg)
        else:
            renpy.invoke_in_thread(self._send, client_socket, msg)

    def _send(self, client_socket: socket.socket, msg: Message):
        try:
            client_socket.send(msg.msg)
        except ConnectionError as e:
            RenServer.logger.warning(f"发送失败：{e}")

    def broadcast(self, msg: Message):
        """调用该方法，向所有客户端发送消息。

        Keyword Arguments:
            msg -- 要发送的消息。
        """            
        
        for client_socket in self.client_socket_dict.values():
            self.send(client_socket, msg)

    def on_conn(self, thread=False):
        """注册一个连接事件。

        Keyword Arguments:
            thread -- 若为True，则该事件将在子线程中执行，用于极为耗时的操作。 (default: {False})
        """

        def decorator(func):
            def wrapper(server: RenServer, client_name: str, client_socket: socket.socket):
                if thread:
                    renpy.invoke_in_thread(func, server, client_name, client_socket)
                else:
                    func(server, client_name, client_socket)
            self.conn_event.append(wrapper)
            return wrapper

        return decorator

    def on_disconn(self, thread=False):
        """注册一个断开连接事件。

        Keyword Arguments:
            thread -- 若为True，则该事件将在子线程中执行，用于极为耗时的操作。 (default: {False})
        """
        
        def decorator(func):
            def wrapper(server: RenServer, client_name: str):
                if thread:
                    renpy.invoke_in_thread(func, server, client_name)
                else:
                    func(server, client_name)
            self.disconn_event.append(wrapper)
            return wrapper

        return decorator

    def on_recv(self, thread=False):
        """注册一个接收消息事件。

        Keyword Arguments:
            thread -- 若为True，则该事件将在子线程中执行，用于极为耗时的操作。 (default: {False})
        """

        def decorator(func):
            def wrapper(server: RenServer, client_name, client_socket: socket.socket, msg: Message):
                if thread:
                    renpy.invoke_in_thread(func, server, client_name, client_socket, msg)
                else:
                    func(server, client_name, client_socket, msg)
            self.recv_event.append(wrapper)
            return wrapper
            
        return decorator
   
    def quit_chat(self):
        """调用该方法，退出聊天模式"""

        preferences.afm_enable = True
        self.chat_mode = False
        self.msg_list.clear()

    def get_message(self, wait_msg: Optional[Message] = None, screen="ren_communicator_chat"):
        """进入聊天模式。该模式将一直运行，直到调用 `quit_chat` 方法退出，该模式适用于简单的两人对话式聊天。

        当没有消息时，会显示等待消息并启用自动前进。若接受到消息，则显示消息并禁用自动前进。
        请使用 `for` 循环获取客户端和消息，并在循环中处理消息。

        Keyword Arguments:
            wait_msg -- 等待消息，当没有消息时显示。若省略该参数则等待时将进入伪阻塞状态 (default: {None})
            screen -- 聊天功能界面 (default: {"ren_communicator_chat"})

        Yields:
            一个元组，包含客户端（当没有消息时为 None）和消息（当没有消息时为等待消息）。
        """

        renpy.notify("进入聊天模式")
        self.chat_mode = True
        self.chat_screen = screen
        renpy.show_screen(screen, self)

        while self.chat_mode:
            if self.msg_list:
                latest_msg = self.msg_list.pop(0)
                preferences.afm_enable = False
                yield latest_msg
            else:
                preferences.afm_enable = True
                if wait_msg:
                    yield (None, wait_msg)
                else:
                    renpy.pause(0)
        
        renpy.hide_screen(screen)
        preferences.afm_enable = False
        renpy.notify("退出聊天模式")
                
    def __enter__(self):
        # 禁止回滚
        config.rollback_enabled = False
        renpy.block_rollback()
        self.run()
        RenServer.logger.info("进入上下文管理器，回滚功能已暂时禁用")
        
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 当退出with语句后恢复禁用的功能
        config.rollback_enabled = True
        renpy.block_rollback()
        self.close()
        RenServer.logger.info("退出上下文管理器，回滚功能已恢复")


class RenClient(object):
    """该类为一个客户端类"""

    logger = set_logger("RenClient", "RenCommunicator.log")

    def __init__(self, target_ip=None, target_port=None, max_data_size=104857600):
        """初始化方法

        Keyword Arguments:
            target_ip -- 服务器IP。 (default: {None})
            target_port -- 服务器端口。 (default: {None})
            max_data_size -- 接收数据的最大大小。默认为100M。 (default: {104857600})
            character -- 该参数应为一个角色对象，用于将字符串消息保存在历史记录中。 (default: {None})
        """                       

        self.target_ip = target_ip
        self.target_port = target_port
        self.target_address = f"{self.target_ip}:{self.target_port}"
        self.max_data_size = max_data_size
        self.socket = None

        self.conn_event = []
        self.disconn_event = []
        self.recv_event = []

        self.chat_mode = False
        self.chat_screen = "ren_communicator_chat"
        self.msg_list: list[Message] = []

    def set_target(self, target_ip, target_port):
        """调用该方法，设置服务器地址。

        Arguments:
            target_ip -- 服务器IP。
            target_port -- 服务器端口。
        """

        self.target_ip = target_ip
        self.target_port = target_port
        self.target_address = f"{self.target_ip}:{self.target_port}"

        return self

    def run(self):
        """调用该方法，开始尝试连接服务器。在快进状态下不会有任何效果"""            

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if renpy.is_skipping():
            return
        renpy.invoke_in_thread(self._connect)

    def close(self):
        """调用该方法，关闭客户端"""

        self.socket.close()   

    def reboot(self):
        """调用该方法，重启客户端"""

        self.close()
        self.run()

    def _connect(self):
        """该方法用于创建连接线程，用于类内部使用，不应被调用"""
        
        while True:
            RenClient.logger.info(f"正在尝试连接到 {self.target_address}")
            try:
                self.socket.connect((self.target_ip, self.target_port))
            except TimeoutError:
                RenClient.logger.warning(f"连接超时，再次尝试连接")
            except OSError:
                RenClient.logger.warning("客户端已被关闭")
                break
            else:
                RenClient.logger.info(f"客户端已连接到 {self.target_address}")
                if self.chat_mode:
                    renpy.show_screen(self.chat_screen, self, True)
                for event in self.conn_event:
                    event(self)
                self._receive()
                break

    def _receive(self):
        """该方法用于接收线程使用，处理接收事件，用于类内部使用，不应被调用"""
        
        while True:
            try:
                data = self.socket.recv(self.max_data_size)
            except ConnectionError:
                RenClient.logger.warning(f"服务器已断开连接")
                if self.chat_mode:
                    renpy.show_screen(self.chat_screen, self, False)
                for event in self.disconn_event:
                    event(self)
                break
            else:
                msg = Message(data)
                if self.chat_mode:
                    self.msg_list.append(msg)
                RenClient.logger.debug(f"接收到服务器的消息：{msg.log_info}")
                for event in self.recv_event:
                    event(self, msg)
    
    def send(self, msg: Message, block=False):
        """调用该方法，向指定客户端发送消息。

        Arguments:
            msg -- 要发送的消息。

        Keyword Arguments:
            block -- 若为True，则该方法将阻塞，直到发送完成。 (default: {False})
        """            
        
        if block:
            self._send(msg)
        else:
            renpy.invoke_in_thread(self._send, msg)

    def _send(self, msg: Message):                  
        
        try:
            self.socket.send(msg.msg)
        except ConnectionError as e:
            RenClient.logger.warning(f"发送失败：{e}")

    def on_conn(self, thread=False):
        """注册一个连接事件。

        Keyword Arguments:
            thread -- 若为True，则该事件将在子线程中执行，用于极为耗时的操作。 (default: {False})
        """

        def decorator(func):
            def wrapper(client: RenClient):
                if thread:
                    renpy.invoke_in_thread(func, client)
                else:
                    func(client)
            self.conn_event.append(wrapper)
            return wrapper

        return decorator

    def on_disconn(self, thread=False):
        """注册一个断开连接事件。

        Keyword Arguments:
            thread -- 若为True，则该事件将在子线程中执行，用于极为耗时的操作。 (default: {False})
        """
        
        def decorator(func):
            def wrapper(client: RenClient):
                if thread:
                    renpy.invoke_in_thread(func, client)
                else:
                    func(client)
            self.disconn_event.append(wrapper)
            return wrapper

        return decorator

    def on_recv(self, thread=False):
        """注册一个接收消息事件。

        Keyword Arguments:
            thread -- 若为True，则该事件将在子线程中执行，用于极为耗时的操作。 (default: {False})
        """

        def decorator(func):
            def wrapper(client: RenClient, msg: Message):
                if thread:
                    renpy.invoke_in_thread(func, client, msg)
                else:
                    func(client, msg)
            self.recv_event.append(wrapper)
            return wrapper
            
        return decorator

    def quit_chat(self):
        """调用该方法，退出聊天模式"""

        preferences.afm_enable = True
        self.chat_mode = False
        self.msg_list.clear()

    def get_message(self, wait_msg: Optional[Message] = None, screen="ren_communicator_chat"):
        """进入聊天模式。该模式将一直运行，直到调用 `quit_chat` 方法退出，该模式适用于简单的两人对话式聊天。

        当没有消息时，会显示等待消息并启用自动前进。若接受到消息，则显示消息并禁用自动前进。
        请使用 `for` 循环获取消息，并在循环中处理消息。

        Keyword Arguments:
            wait_msg -- 等待消息，当没有消息时显示。若省略该参数则等待时将进入伪阻塞状态 (default: {None})
            screen -- 聊天功能界面 (default: {"ren_communicator_chat"})

        Yields:
            一个消息对象。
        """

        renpy.notify("进入聊天模式")
        self.chat_mode = True
        self.chat_screen = screen
        renpy.show_screen(screen, self)

        while self.chat_mode:
            if self.msg_list:
                preferences.afm_enable = False
                yield self.msg_list.pop(0)
            else:
                preferences.afm_enable = True
                if wait_msg:
                    yield wait_msg
                else:
                    renpy.pause(0)
        
        renpy.hide_screen(screen)
        preferences.afm_enable = False
        renpy.notify("退出聊天模式")

    def __enter__(self):
        config.rollback_enabled = False
        renpy.block_rollback()
        self.run()
        RenClient.logger.info("进入上下文管理器，回滚功能已暂时禁用")
        
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        config.rollback_enabled = True
        renpy.block_rollback()
        self.close()
        RenClient.logger.info("退出上下文管理器，回滚功能已恢复")
