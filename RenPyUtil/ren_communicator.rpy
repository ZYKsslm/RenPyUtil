# 此文件提供了一系列基于Ren'Py的功能类，以供Ren'Py开发者调用
# 作者  ZYKsslm
# 仓库  https://github.com/ZYKsslm/RenPyUtil
# 声明  该源码使用 MIT 协议开源，但若使用需要在程序中标明作者消息


init -1 python:

    from datetime import datetime
    import socket

    class Prompt(object):
        """命令类"""        

        def __init__(self, encode, *prompts):
            if encode:
                prompts = list(prompts)
                for a in range(len(prompts)):
                    prompts[a] = prompts[a].encode("utf-8")
            
            self.prompts = set(prompts)


    class RenServer(object):
        """该类为一个服务端类。基于socket进行多线程通信。

        在在子线程中运行的方法中使用renpy更新屏幕的函数（如`renpy.say()`、`renpy.call_screen()`等），可能引发异常。

        在子线程中运行的方法有：
            1. 使用`set_prompt`设定的命令方法。
            2. 使用`set_receive_event``set_conn_event``set_error_event`设定的事件方法。
            3. 所有进行通信的方法。
        """

        # 支持监听的事件
        EVENT = [
            "PROMPT",   # 命令事件
            "ERROR",    # 异常事件
            "CONNECT",  # 连接事件
            "RECEIVE",  # 接收事件
        ]

        PROMPT_EVENT = "PROMPT",
        ERROR_EVENT = "ERROR",
        CONNECT_EVENT = "CONNECT",
        RECEIVE_EVENT = "RECEIVE"
        

        def __init__(self, max_conn=5, max_data_size=1024, ip="0.0.0.0", port=8888):
            """初始化方法。

            Keyword Arguments:
                max_conn -- 最大连接数。 (default: {5})
                max_data_size -- 接收数据的最大大小。 (default: {1024})
                port -- 端口号。 (default: {None})
            """            

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.port = port
            self.ip = ip
            self.max_data_size = max_data_size
            self.max_conn = max_conn
            self.socket.bind((self.ip, self.port))

            self.client_socket_list = []
            self.has_communicated = False
            self.current_prompt = None
            self.received = False
            self.reply = None

            self.prompt_dict = {}
            self.error_event = []
            self.receive_event = []
            self.conn_event = []

            self.error_log = {}

        def set_prompt(self, prompt: str | list | Prompt, func: function, encode=True, *args, **kwargs):
            """调用该方法，创建一个命令，当接收到该命令后执行绑定的函数。命令将作为第一个参数，客户端socket将作为第二个参数传入指定函数中。

            不定参数为绑定的函数参数。

            Arguments:
                prompt -- 命令语句。可为一个字符串或一个列表或一个Prompt对象，若为列表，则列表中所有命令都可触发命令。
                func -- 一个函数。

            Keyword Arguments:
                encode -- 是否编码。 (default: {True})
            """ 

            if not isinstance(prompt, Prompt):
                prompt = Prompt(encode, prompt)
            
            self.prompt_dict[prompt] = [func, args, kwargs]

        def set_reply(self, reply):
            """调用该方法，指定接收到消息后自动回复的消息。

            Arguments:
                reply -- 要回复的消息。
            """       

            self.reply = reply

        def set_error_event(self, func: function, *args, **kwargs):
            """调用该方法，指定当通信出现异常时的行为。异常信息将作为第一个参数传入指定函数中。

            不定参数为绑定的函数参数。

            Arguments:
                func 一个函数
            """            

            self.error_event = [func, args, kwargs]

        def set_receive_event(self, func: function, *args, **kwargs):
            """调用该方法，指定当接受到消息时的行为。接收到的数据将作为第一个参数，客户端socket将作为第二个参数传入指定函数中。

            不定参数为绑定的函数参数。

            Arguments:
                func -- 一个函数。
            """            

            self.receive_event = [func, args, kwargs]

        def set_conn_event(self, func: function, *args, **kwargs):
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
                try:
                    for s in self.client_socket_list:
                        s.close()    
                except socket.error:
                    pass

        def close_a_conn(self, client_socket: socket.socket=None):
            """调用该方法，关闭一个指定socket连接。

            Keyword Arguments:
                socket -- 客户端socket。若该参数不填，则关闭最新的连接。 (default: {None})
            """    

            if client_socket:
                client_socket.close()
            else:
                try:
                    self.client_socket_list[len(self.client_socket_list)-1].close()    
                except IndexError or socket.err:
                    pass

        def listen_event(self, event, tip="", prompt=None):
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

            elif event == RenServer.ERROR_EVENT:
                event_counter = len(self.error_log)
                while len(self.error_log) <= event_counter:
                    renpy.notify(tip)
                    renpy.pause()

            elif event == RenServer.CONNECT_EVENT:
                event_counter = len(server.client_socket_list)
                while len(server.client_socket_list) <= event_counter:
                    renpy.notify(tip)
                    renpy.pause()

            elif event == RenServer.RECEIVE_EVENT:
                while not self.received:
                    renpy.notify(tip)
                    renpy.pause()

            else:
                return

        def run(self):
            """调用该方法，开始监听端口，创建连接线程。"""            

            self.has_communicated = True
            self.socket.listen(self.max_conn)
            renpy.invoke_in_thread(self._accept)

        def reboot(self, log_clear=False):
            """调用该方法将重新开始通信。

            Keyword Arguments:
                log_clear -- 若为True，将清除错误日志。 (default: {False})
            """            

            self.close()
            self.close_all_conn()
            if log_clear:
                self.error_log.clear()
            self.run()

        def _accept(self):
            """该方法用于创建连接线程，用于类内部使用，不应被调用。"""            

            while True:
                try:
                    client_socket, address = self.socket.accept()
                except Exception as err:
                    self.error_log[datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")] = err
                    return

                if self.conn_event:
                    func, args, kwargs = self.conn_event
                    renpy.invoke_in_thread(func, client_socket, *args, **kwargs)

                self.client_socket_list.append(client_socket)
                renpy.invoke_in_thread(self._receive, client_socket, self.max_data_size)

        def _receive(self, client_socket: socket.socket, max_data_size):
            """该方法用于接收线程使用，处理接收事件，用于类内部使用，不应被调用。"""
            
            while True:
                self.received = False
                try:
                    data = client_socket.recv(max_data_size)
                    self.received = True
                except Exception as err:
                    self.received = False
                    self.error_log[datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")] = err
                    client_socket.close()
                    self.client_socket_list.remove(client_socket)

                    if self.error_event:
                        func, args, kwargs = self.error_event
                        renpy.invoke_in_thread(func, err, *args, **kwargs)

                    return
                
                for prompt in self.prompt_dict.keys():
                    if data in prompt.prompts:
                        func, args, kwargs = self.prompt_dict[prompt]
                        self.current_prompt = prompt
                        renpy.invoke_in_thread(func, data, client_socket, *args, **kwargs)

                if self.reply:
                    try:
                        client_socket.send(self.reply)
                    except Exception as err:
                        self.error_log[datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")] = err
                        client_socket.close()
                        self.client_socket_list.remove(client_socket)
                        return

                if self.receive_event:
                    func, args, kwargs = self.receive_event
                    renpy.invoke_in_thread(func, data, client_socket, *args, **kwargs)

        def send(self, client_socket: socket.socket, msg):
            """调用该方法，向指定客户端发送消息。该方法为阻塞方法。

            Arguments:
                client_socket -- 客户端socket。

            Keyword Arguments:
                msg -- 要发送的消息。

            Returns:
                若返回值为True，则发送消息成功；若为False则失败。
            """            
            
            try:
                client_socket.send(msg)
            except Exception as err:
                self.error_log[datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")] = err
                client_socket.close()
                self.client_socket_list.remove(client_socket)

                if self.error_event:
                    func, args, kwargs = self.error_event
                    renpy.invoke_in_thread(func, err, *args, **kwargs)

                return False
            else:
                return True

        def __enter__(self):
            # 进入with语句后执行的方法
            # 防止用户回滚游戏重复启动线程
            # 禁止用户存档
            # 禁止用户跳过
            config.rollback_enabled = False
            config.allow_skipping = False
            renpy.block_rollback()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            # 当退出with语句后允许回滚
            config.rollback_enabled = True
            renpy.block_rollback()
            config.allow_skipping = True
    

    class RenClient(object):
        """该类为一个客户端类。
        
        在在子线程中运行的方法中使用renpy更新屏幕的函数（如`renpy.say()`、`renpy.call_screen()`等），可能引发异常。

        在子线程中运行的方法有：
            1. 使用`set_prompt`设定的命令方法。
            2. 使用`set_receive_event``set_conn_event``set_error_event`设定的事件方法。
            3. 所有进行通信的方法。
        """

        # 支持监听的事件
        EVENT = [
            "PROMPT",   # 命令事件
            "ERROR",    # 异常事件
            "CONNECT",  # 连接事件
            "RECEIVE",  # 接收事件
        ]

        PROMPT_EVENT = "PROMPT",
        ERROR_EVENT = "ERROR",
        CONNECT_EVENT = "CONNECT",
        RECEIVE_EVENT = "RECEIVE"

        
        def __init__(self, target_ip, target_port, max_data_size=1024):
            """初始化方法。

            Arguments:
                target_ip -- 服务端IP。
                target_port -- 服务端端口。

            Keyword Arguments:
                max_data_size -- 接收数据的最大大小。 (default: {1024})
            """                       

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.target_ip = target_ip
            self.target_port = target_port
            self.max_data_size = max_data_size

            self.is_conn = False
            self.has_communicated = False
            self.received = False
            self.current_prompt = None
            self.reply = None

            self.prompt_dict = {}
            self.error_event = []
            self.receive_event = []
            self.conn_event = []

            self.error_log = {}

        def set_prompt(self, prompt: str | set, func: function, encode=True, *args, **kwargs):
            """调用该方法，创建一个命令，当客户端发送该命令后执行绑定的函数。命令将作为第一个参数，客户端socket将作为第二个参数传入指定函数中。

            不定关键字参数为函数参数。

            Arguments:
                prompt -- 命令语句。可为一个字符串或一个集合，若为集合，则集合中所有语句都可触发命令。
                func -- 一个函数。

            Keyword Arguments:
                encode -- 是否自动编码。 (default: {True})
            """ 

            if not isinstance(prompt, Prompt):
                prompt = Prompt(encode, prompt)
            
            self.prompt_dict[prompt] = [func, args, kwargs]

        def set_reply(self, reply):
            """调用该方法，当接收到消息时自动回复指定的消息。

            Arguments:
                reply -- 要回复的消息。
            """       

            self.reply = reply

        def set_error_event(self, func: function, *args, **kwargs):
            """调用该方法，指定当通信出现异常时的行为。异常信息将作为第一个参数传入指定函数中。

            不定参数为绑定的函数参数。

            Arguments:
                func 一个函数
            """            

            self.error_event = [func, args, kwargs]

        def set_receive_event(self, func: function, *args, **kwargs):
            """调用该方法，指定当接受到消息时的行为。接收到的数据将作为第一个参数。

            不定关键字参数为函数参数。

            Arguments:
                func -- 一个函数。
            """            

            self.receive_event = [func, args, kwargs]

        def set_conn_event(self, func: function, *args, **kwargs):
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

            elif event == RenClient.ERROR_EVENT:
                event_counter = len(self.error_log)
                while len(self.error_log) <= event_counter:
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
                self.error_log.clear()
            self.run()  

        def _connect(self):
            """该方法用于创建连接线程，用于类内部使用，不应被调用。"""

            try:
                self.socket.connect((self.target_ip, self.target_port))
                self.is_conn = True
            except Exception as err:
                self.error_log[datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")] = err
                self.is_conn = False
                if self.error_event:
                    func, args, kwargs = self.error_event
                    renpy.invoke_in_thread(func, err, *args, **kwargs)
                return

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
                except Exception as err:
                    self.received = False
                    self.error_log[datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")] = err
                    self.socket.close()
                    self.is_conn = False

                    if self.error_event:
                        func, args, kwargs = self.error_event
                        renpy.invoke_in_thread(func, err, *args, **kwargs)

                    return

                for prompt in self.prompt_dict.keys():
                    if data in prompt.prompts:
                        func, args, kwargs = self.prompt_dict[prompt]
                        self.current_prompt = prompt
                        renpy.invoke_in_thread(func, data, client_socket, *args, **kwargs)

                if self.reply:
                    res = self.socket.send()
                    if not res:
                        self.is_conn = res
                        return

                if self.receive_event:
                    func, args, kwargs = self.receive_event
                    renpy.invoke_in_thread(func, data, *args, **kwargs)                

        def send(self, msg):
            """调用该方法，向指定客户端发送消息。该方法为阻塞方法。

            Arguments:
                msg -- 要发送的消息。

            Returns:
                若为True则发送成功；若为False则发送失败。
            """                     
            try:
                self.socket.send(msg)
            except Exception as err:
                self.error_log[datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")] = err

                if self.error_event:
                    func, args, kwargs = self.error_event
                    renpy.invoke_in_thread(func, err, *args, **kwargs)

                return False
            else:
                return True

        def __enter__(self):
            config.rollback_enabled = False
            config.allow_skipping = False
            renpy.block_rollback()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            config.rollback_enabled = True
            config.allow_skipping = True
            renpy.block_rollback()