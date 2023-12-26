# 此文件提供了一系列基于Ren'Py的功能类，以供Ren'Py开发者调用
# 作者  ZYKsslm
# 仓库  https://github.com/ZYKsslm/RenPyUtil
# 声明  该源码使用 MIT 协议开源，但若使用需要在程序中标明作者消息


"""renpy
init -1 python:
"""


from datetime import datetime
import socket
import pickle
import os


class Message(object):
    """消息类，用于定义通信中收发的消息对象。"""

    STRING = "string"
    FILE = "file"
    IMAGE = "image"
    VOICE = "voice"

    def __init__(self, message: str, _type="string"):
        """初始化方法。

        Arguments:
            message -- 可能为一个纯字符串的消息，或一个文件的路径。
            _type -- 文件类型。应为`Message.STRING` `Message.IMAGE` `Message.VOICE` `Message.FILE`其中一项。
        """        
        
        self.type = _type
        self.message = message
        
        if self.type == Message.STRING:
            self.data = self.message.encode("utf-8")
            self.format = None
        else:
            if not os.path.exists(self.message):
                raise Exception(f"找不到该文件：{self.message}")
            
            self.format = os.path.splitext(self.message)[1]
            
            with open(self.message, "rb") as f:
                self.data = f.read()
        
        self.info = pickle.dumps(
            {
                "message": self.message,
                "data": self.data,
                "type": self.type,
                "format": self.format
            }
        )


class Prompt(object):
    """命令类。"""        

    def __init__(self, *prompts):
        prompts = list(prompts)
        for a in range(len(prompts)):
            prompts[a] = prompts[a].encode("utf-8")
        
        # 转换为一个集合
        self.prompts = set(prompts)
        
        
class _HistoryEntry(object):
    def __init__(self, kind, who, what, who_args, what_args, window_args, show_args):
        self.kind = kind
        self.who = who
        self.what = what
        self.what_args = what_args
        self.who_args = who_args
        self.window_args = window_args
        self.show_args = show_args


class RenServer(object):
    """该类为一个服务端类。基于socket进行多线程通信。

    在于子线程中运行的方法中使用renpy某些更新屏幕的函数（如`renpy.say()`等），可能会引发异常。

    在子线程中运行的方法有:
        1. 使用`set_prompt`设定的命令方法。
        2. 使用`set_receive_event` `set_conn_event` `set_disconn_event`设定的事件方法。
        3. 所有进行通信的方法。
    """

    # 支持监听的事件
    EVENT = [
        "PROMPT",   # 命令事件
        "DISCONN",    # 断连事件
        "CONNECT",  # 连接事件
        "RECEIVE",  # 接收事件
    ]

    PROMPT_EVENT = "PROMPT"
    DISCONN_EVENT = "DISCONN"
    CONNECT_EVENT = "CONNECT"
    RECEIVE_EVENT = "RECEIVE"
    

    def __init__(self, max_conn=5, max_data_size=104857600, ip="0.0.0.0", port=8888, history=False, character=None):
        """初始化方法。

        Keyword Arguments:
            max_conn -- 最大连接数。 (default: {5})
            max_data_size -- 接收数据的最大大小。默认为100M。 (default: {104857600})
            port -- 端口号。 (default: {None})
            history -- 接收到的文字消息是否显示在历史记录中。 (default: {False})
            character -- 若`history`参数为True，则该参数应为一个角色对象，用于保存在历史记录中。 (default: {None})
        """            

        self.port = port
        self.ip = ip
        self.max_data_size = max_data_size
        self.max_conn = max_conn
        self.history = history
        self.character = character
        
        self.bind()

        self.client_socket_list = []
        self.has_communicated = False
        self.current_prompt = None
        self.received = False
        self.reply = None

        self.prompt_dict = {}
        self.disconn_event = []
        self.receive_event = []
        self.conn_event = []

        self.log = {}

    def set_prompt(self, prompt: str | list | Prompt, func, *args, **kwargs):
        """调用该方法，创建一个命令，当接收到该命令后执行绑定的函数。命令将作为第一个参数，客户端socket将作为第二个参数传入指定函数中。

        不定参数为绑定的函数参数。

        Arguments:
            prompt -- 命令语句。可为一个字符串或一个列表或一个Prompt对象，若为列表，则列表中所有命令都可触发命令。
            func -- 一个函数。
        """ 

        if not isinstance(prompt, Prompt):
            prompt = Prompt(prompt)
        
        self.prompt_dict[prompt] = [func, args, kwargs]

    def set_reply(self, reply: str | Message):
        """调用该方法，指定接收到消息后自动回复的消息。

        Arguments:
            reply -- 要回复的消息。
        """       
        
        if not isinstance(reply, Message):
            reply = Message(reply)

        self.reply = reply

    def set_disconn_event(self, func, *args, **kwargs):
        """调用该方法，指定当断开连接时的行为。断连的主机名称（一个元组）将作为第一个参数传入指定函数中。

        不定参数为绑定的函数参数。

        Arguments:
            func 一个函数
        """            

        self.disconn_event = [func, args, kwargs]

    def set_receive_event(self, func, *args, **kwargs):
        """调用该方法，指定当接受到消息时的行为。接收到的数据将作为第一个参数，客户端socket将作为第二个参数传入指定函数中。

        不定参数为绑定的函数参数。

        Arguments:
            func -- 一个函数。
        """      

        self.receive_event = [func, args, kwargs]

    def set_conn_event(self, func, *args, **kwargs):
        """调用该方法，指定当客户端连接后的行为。客户端socket将作为第一个参数传入指定函数中。

        不定参数为绑定的函数参数。

        Arguments:
            func -- 一个函数。
        """            

        self.conn_event = [func, args, kwargs]
    
    def close(self):
        """调用该方法，关闭服务端。"""

        self.socket.close()     

    def close_all_conn(self):
        """调用该方法，关闭所有连接。"""   

        if self.client_socket_list:
            for i in range(len(self.client_socket_list)):
                socket = self.client_socket_list[i]
                self.close_a_conn(socket)

    def close_a_conn(self, client_socket: socket.socket=None):
        """调用该方法，关闭一个指定socket连接。

        Keyword Arguments:
            socket -- 客户端socket。若该参数不填，则关闭最新的连接。 (default: {None})
        """    

        try:
            if client_socket:
                client_socket.close()
                self.client_socket_list.remove(client_socket)
            else:
                index = len(self.client_socket_list)-1
                socket = self.client_socket_list[index]
                socket.close()
                self.client_socket_list.remove(socket) 
        except:
            pass

    def listen_event(self, event, tip="", prompt: Prompt = None):
        """调用该方法阻塞式监听一个事件，监听到事件后取消阻塞。

        Arguments:
            event -- 事件类型。

        Keyword Arguments:
            prompt -- 若为命令事件，则该参数为一个Prompt对象。 (default: {None})
            tip -- renpy提示界面的内容。 (default: {None})
        """            

        if event == RenServer.PROMPT_EVENT:
            while prompt != self.current_prompt:
                renpy.notify(tip)
                renpy.pause()

        elif event == RenServer.DISCONN_EVENT:
            event_counter = len(self.log)
            while len(self.log) <= event_counter:
                renpy.notify(tip)
                renpy.pause()

        elif event == RenServer.CONNECT_EVENT:
            event_counter = len(self.client_socket_list)
            while len(self.client_socket_list) <= event_counter:
                renpy.notify(tip)
                renpy.pause()

        elif event == RenServer.RECEIVE_EVENT:
            while not self.received:
                renpy.notify(tip)
                renpy.pause()

        else:
            return
    
    def bind(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.socket.bind((self.ip, self.port))
    
    def run(self):
        """调用该方法，开始监听端口，创建连接线程。"""            
        
        try:
            self.socket.listen(self.max_conn)
        except socket.error:
            self.bind()
            self.socket.listen(self.max_conn)

        self.has_communicated = True
        renpy.invoke_in_thread(self._accept)

    def reboot(self, log_clear=False):
        """调用该方法将重新开始通信。

        Keyword Arguments:
            log_clear -- 若为True，将清除日志。 (default: {False})
        """            

        self.close()
        self.close_all_conn()
        if log_clear:
            self.log.clear()
        self.run()

    def _accept(self):
        """该方法用于创建连接线程，用于类内部使用，不应被调用。"""            

        while True:
            client_socket = self.socket.accept()[0]
    
            self.client_socket_list.append(client_socket)
            renpy.invoke_in_thread(self._receive, client_socket, self.max_data_size)

            if self.conn_event:
                func, args, kwargs = self.conn_event
                renpy.invoke_in_thread(func, client_socket, *args, **kwargs)

    def _receive(self, client_socket: socket.socket, max_data_size):
        """该方法用于接收线程使用，处理接收事件，用于类内部使用，不应被调用。"""
            
        while True:
            self.received = False
            try:
                data = client_socket.recv(max_data_size)
                self.received = True
            except socket.error as err:
                self.log[datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")] = err
                self.client_socket_list.remove(client_socket)

                if self.disconn_event:
                    func, args, kwargs = self.disconn_event
                    renpy.invoke_in_thread(func, client_socket.getpeername(), *args, **kwargs)

                client_socket.close()
                return
            
            info = pickle.loads(data)
            data = info["data"]
            
            for prompt in self.prompt_dict.keys():
                if data in prompt.prompts:
                    func, args, kwargs = self.prompt_dict[prompt]
                    self.current_prompt = prompt
                    renpy.invoke_in_thread(func, data, client_socket, *args, **kwargs)

            if self.reply:
                self.send(client_socket, self.reply)

            if self.receive_event:
                func, args, kwargs = self.receive_event
                renpy.invoke_in_thread(func, info, client_socket, *args, **kwargs)
               
            if self.history and info["type"] == Message.STRING: 
                history_obj = _HistoryEntry(
                    kind="adv",
                    who=self.character.name,
                    what=info["message"],
                    who_args=self.character.who_args,
                    what_args=self.character.what_args,
                    window_args=self.character.window_args,
                    show_args=self.character.show_args
                )
                _history_list.append(history_obj)

    def send(self, client_socket: socket.socket, msg: Message):
        """调用该方法，向指定客户端发送消息。该方法为阻塞方法。

        Arguments:
            client_socket -- 客户端socket。

        Keyword Arguments:
            msg -- 要发送的消息。

        Returns:
            若返回值为True，则发送消息成功；若为False则失败。
        """            
        
        try:
            client_socket.send(msg.info)
        except socket.error as err:
            self.log[datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")] = err
            
            try:
                self.client_socket_list.remove(client_socket)
            except:
                pass

            if self.disconn_event:
                func, args, kwargs = self.disconn_event
                renpy.invoke_in_thread(func, client_socket.getpeername(), *args, **kwargs)

            client_socket.close()
            return False
        else:
            return True

    def __enter__(self):
        # 进入with语句后执行的方法
        # 禁止了一些功能防止造成与线程有关的异常
        # 禁止回滚
        # 禁止自动存档
        # 禁止用户存档
        # 禁止用户跳过
        config.rollback_enabled = False
        config.allow_skipping = False
        config.has_autosave = False
        renpy.block_rollback()
        
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 当退出with语句后恢复禁用的功能
        config.rollback_enabled = True
        config.allow_skipping = True
        config.has_autosave = True
        renpy.block_rollback()


class RenClient(object):
    """该类为一个客户端类。
    
    在于子线程中运行的方法中使用renpy更新屏幕的函数（如`renpy.say()`等），可能会引发异常。

    在子线程中运行的方法有：
        1. 使用`set_prompt`设定的命令方法。
        2. 使用`set_receive_event` `set_conn_event` `set_disconn_event`设定的事件方法。
        3. 所有进行通信的方法。
    """

    # 支持监听的事件
    EVENT = [
        "PROMPT",   # 命令事件
        "DISCONN",    # 断连事件
        "CONNECT",  # 连接事件
        "RECEIVE",  # 接收事件
    ]

    PROMPT_EVENT = "PROMPT"
    DISCONN_EVENT = "DISCONN"
    CONNECT_EVENT = "CONNECT"
    RECEIVE_EVENT = "RECEIVE"

    
    def __init__(self, target_ip, target_port, max_data_size=104857600, history=False, character=None):
        """初始化方法。

        Arguments:
            target_ip -- 服务端IP。
            target_port -- 服务端端口。

        Keyword Arguments:
            max_data_size -- 接收数据的最大大小。默认为100M。 (default: {104857600})
            history -- 接收到的文字消息是否显示在历史记录中。 (default: {False})
            character -- 若`history`参数为True，则该参数应为一个角色对象，用于保存在历史记录中。 (default: {None})
        """                       

        self.target_ip = target_ip
        self.target_port = target_port
        self.max_data_size = max_data_size
        self.history = history
        self.character = character
        
        self.bind()

        self.is_conn = False
        self.has_communicated = False
        self.received = False
        self.current_prompt = None
        self.reply = None

        self.prompt_dict = {}
        self.disconn_event = []
        self.receive_event = []
        self.conn_event = []

        self.log = {}

    def set_prompt(self, prompt: str | set, func, *args, **kwargs):
        """调用该方法，创建一个命令，当服务端发送该命令后执行绑定的函数。命令将作为第一个参数传入指定函数中。

        不定关键字参数为函数参数。

        Arguments:
            prompt -- 命令语句。可为一个字符串或一个集合，若为集合，则集合中所有语句都可触发命令。
            func -- 一个函数。
        """ 

        if not isinstance(prompt, Prompt):
            prompt = Prompt(prompt)
        
        self.prompt_dict[prompt] = [func, args, kwargs]

    def set_reply(self, reply: str | Message):
        """调用该方法，指定接收到消息后自动回复的消息。

        Arguments:
            reply -- 要回复的消息。
        """       
        
        if not isinstance(reply, Message):
            reply = Message(reply)

        self.reply = reply

    def set_disconn_event(self, func, *args, **kwargs):
        """调用该方法，指定当断开连接时的行为。

        不定参数为绑定的函数参数。

        Arguments:
            func 一个函数
        """            

        self.disconn_event = [func, args, kwargs]

    def set_receive_event(self, func, *args, **kwargs):
        """调用该方法，指定当接受到消息时的行为。接收到的数据将作为第一个参数传入指定函数中。

        不定关键字参数为函数参数。

        Arguments:
            func -- 一个函数。
        """            

        self.receive_event = [func, args, kwargs]

    def set_conn_event(self, func, *args, **kwargs):
        """调用该方法，指定成功连接服务端后的行为。

        不定关键字参数为函数参数。

        Arguments:
            func -- 一个函数。
        """            

        self.conn_event = [func, args, kwargs]

    def listen_event(self, event, tip="", prompt=None):
        """调用该方法阻塞式监听一个事件，监听到事件后取消阻塞。

        Arguments:
            event -- 事件类型。

        Keyword Arguments:
            prompt -- 若为命令事件，则该参数为一个Prompt对象。 (default: {None})
            tip -- renpy提示界面的内容。 (default: {None})
        """            

        if event == RenClient.PROMPT_EVENT:
            while prompt != self.current_prompt:
                renpy.notify(tip)
                renpy.pause()

        elif event == RenClient.DISCONN_EVENT:
            event_counter = len(self.log)
            while len(self.log) <= event_counter:
                renpy.notify(tip)
                renpy.pause()

        elif event == RenClient.CONNECT_EVENT:
            while not self.is_conn:
                renpy.notify(tip)
                renpy.pause()

        elif event == RenClient.RECEIVE_EVENT:
            while not self.received:
                renpy.notify(tip)
                renpy.pause()

        else:
            return
        
    def bind(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        """调用该方法，开始尝试连接服务端。"""            
        
        self.has_communicated = True
        renpy.invoke_in_thread(self._connect)

    def close(self):
        """调用该方法，关闭客户端。"""

        self.socket.close()   

    def reboot(self, log_clear=False):
        """调用该函数重新开始通信。"""

        self.close()
        if log_clear:
            self.log.clear()
        self.run()  
    
    def reconn(self):
        """调用该方法，尝试重新连接。"""
        
        self.socket.close()
        self.bind()
        self._connect()        

    def _connect(self):
        """该方法用于创建连接线程，用于类内部使用，不应被调用。"""

        while True:
            try:
                self.socket.connect((self.target_ip, self.target_port))
                self.is_conn = True
            except socket.error:
                continue
            else:
                break

        if self.conn_event:
            func, args, kwargs = self.conn_event
            renpy.invoke_in_thread(func, *args, **kwargs)
        
        self._receive()

    def _receive(self):
        """该方法用于接收线程使用，处理接收事件，用于类内部使用，不应被调用。"""
        
        while True:
            self.received = False
            try:
                data = self.socket.recv(self.max_data_size)
                self.received = True
            except socket.error as err:
                self.received = False
                self.log[datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")] = err
                self.is_conn = False

                if self.disconn_event:
                    func, args, kwargs = self.disconn_event
                    renpy.invoke_in_thread(func, *args, **kwargs)

                self.reconn()
            
            info = pickle.loads(data)
            data = info["data"]

            for prompt in self.prompt_dict.keys():
                if data in prompt.prompts:
                    func, args, kwargs = self.prompt_dict[prompt]
                    self.current_prompt = prompt
                    renpy.invoke_in_thread(func, data, *args, **kwargs)

            if self.reply:
                self.send(self.reply)

            if self.receive_event:
                func, args, kwargs = self.receive_event
                renpy.invoke_in_thread(func, info, *args, **kwargs)     
                
            if self.history and info["type"] == Message.STRING: 
                history_obj = _HistoryEntry(
                    kind="adv",
                    who=self.character.name,
                    what=info["message"],
                    who_args=self.character.who_args,
                    what_args=self.character.what_args,
                    window_args=self.character.window_args,
                    show_args=self.character.show_args
                )
                _history_list.append(history_obj)        

    def send(self, msg: Message):
        """调用该方法，向指定客户端发送消息。该方法为阻塞方法。

        Arguments:
            msg -- 要发送的消息。

        Returns:
            若为True则发送成功；若为False则发送失败。
        """                     
        
        try:
            self.socket.send(msg.info)
        except socket.error as err:
            self.log[datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")] = err

            if self.disconn_event:
                func, args, kwargs = self.disconn_event
                renpy.invoke_in_thread(func, *args, **kwargs)

            return False
        else:
            return True

    def __enter__(self):
        config.rollback_enabled = False
        config.allow_skipping = False
        config.has_autosave = False
        renpy.block_rollback()
        
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        config.rollback_enabled = True
        config.allow_skipping = True
        config.has_autosave = True
        renpy.block_rollback()