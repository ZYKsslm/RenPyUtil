# 此文件提供了一系列基于Ren'Py的功能类，以供Ren'Py开发者调用
# 作者  ZYKsslm
# 仓库  https://github.com/ZYKsslm/RenPyUtil
# 声明  该源码使用 MIT 协议开源，但若使用需要在程序中标明作者消息


init python:

    from datetime import datetime
    import socket
    import threading


    class RenServer(object):
        """该类为一个服务端类。基于socket进行多线程通信。

        若重写该类中的方法并使用renpy中有阻塞操作的语句可能导致程序异常。
        """
        
        def __init__(self, max_conn=5, max_data_size=1024, port=8888):
            """初始化方法。

            Keyword Arguments:
                max_conn -- 最大连接数。 (default: {5})
                max_data_size -- 接收数据的最大大小。 (default: {1024})
                port -- 端口号。 (default: {None})
            """            

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.port = port
            self.max_data_size = max_data_size
            self.max_conn = max_conn
            self.socket.bind(("", self.port))

            self.main_thread = None
            self.data = None
            self.reply = None
            self.auto_decode = True

            self.prompt_dict = {}
            self.prompt_return_dict = {}
            self.client_socket_list = []
            self.conn_thread_list = []

            self.receive_event = ()
            self.conn_event = ()
            self.event_func_return = {}

            self.error_log = {}

        def set_prompt(self, prompt: str | set, func: function, **kwargs):
            """调用该方法，创建一个命令，当客户端发送该命令后执行绑定的函数。命令将作为第一个参数，客户端socket将作为第二个参数传入指定函数中。
            
            若函数有返回值，返回值储存在对象的`prompt_return_dict`实例属性中，该属性为一个键为命令，值为命令返回值的字典。

            不定关键字参数为函数参数。

            Arguments:
                prompt -- 命令语句。可为一个字符串或一个集合，若为集合，则集合中所有语句都可触发命令。
                func -- 一个函数。
            """ 

            if isinstance(prompt, set):
                for p in prompt:
                    self.prompt_dict[p] = (func, kwargs)
            else:
                self.prompt_dict[prompt] = (func, kwargs)

        def set_reply(self, reply):
            """调用该方法，当接收到消息时自动回复指定的消息。

            Arguments:
                reply -- 要回复的消息。
            """       

            self.reply = reply

        def set_receive_event(self, func: function, **kwargs):
            """调用该方法，指定当接受到消息时的行为。接收到的数据将作为第一个参数，客户端socket将作为第二个参数传入指定函数中。

            若函数有返回值，则返回值储存在对象的`prompt_return_dict`实例属性中。该事件返回值的键为`receive`。

            不定关键字参数为函数参数。

            Arguments:
                func -- 一个函数。
            """            

            self.receive_event = (func, kwargs)

        def set_conn_event(self, func: function, **kwargs):
            """调用该方法，指定当客户端连接后的行为。客户端socket将作为第一个参数传入指定函数中。

            若函数有返回值，则返回值储存在对象的`prompt_return_dict`实例属性中。该事件返回值的键为`conn`。

            不定关键字参数为函数参数。

            Arguments:
                func -- 一个函数。
            """            

            self.conn_event = (func, kwargs)

        def run(self):
            """调用该方法，开始监听端口，等待连接。"""            

            self.socket.listen(self.max_conn)
            self.main_thread = threading.Thread(target=self._accept)
            self.main_thread.daemon = True
            self.main_thread.start()

        def reboot(self):
            """调用该函数，重新开始通信并清除错误日志。"""

            self.close()
            self.close_all_conn()
            self.error_log = {}
            self.run()            

        def close(self):
            """调用该方法，关闭服务端。"""

            self.socket.close()     

        def close_all_conn(self):
            """调用该方法，关闭所有连接并结束所有线程。"""   

            if self.client_socket_list:
                try:
                    for s in self.client_socket_list:
                        s.close()    
                except socket.error:
                    pass

        def close_a_conn(self, client_socket: socket.socket=None):
            """调用该方法，关闭一个指定连接并结束线程。

            Keyword Arguments:
                socket -- 客户端socket。若该参数不填，则关闭最新的连接。 (default: {None})
            """    

            if client_socket:
                client_socket.close()
            else:
                self.client_socket_list[len(self.client_socket_list)-1].close()             

        def _accept(self):
            """该方法用于创建连接线程，用于类内部使用，不应被调用。"""            

            while True:
                try:
                    client_socket, address = self.socket.accept()
                except socket.error as err:
                    self.error_log[datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")] = err
                    return

                if self.conn_event:
                    func, kwargs = self.conn_event
                    func_return = func(client_socket, **kwargs)

                    if func_return is not None:
                        self.event_func_return["conn"] = func_return

                self.client_socket_list.append(client_socket)
                receive_thread = threading.Thread(target=self._receive, args=(client_socket, self.max_data_size))
                self.conn_thread_list.append(receive_thread)
                receive_thread.daemon = True
                receive_thread.start()

        def _receive(self, client_socket: socket.socket, max_data_size):
            """该方法用于创建接收线程，处理接收事件。用于类内部使用，不应被调用。"""
            
            while True:
                try:
                    data = client_socket.recv(max_data_size)
                    if self.auto_decode:
                        data = data.decode("utf-8")
                except socket.error as err:
                    self.error_log[datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")] = err
                    client_socket.close()
                    self.client_socket_list.remove(client_socket)
                    return

                if data in self.prompt_dict.keys():
                    func, kwargs = self.prompt_dict[data]
                    func_return = func(data, client_socket, **kwargs)

                    if func_return is not None:
                        self.prompt_return_dict[data] = func_return

                if self.reply:
                    res = self.send(client_socket)
                    if not res:
                        self.client_socket_list.remove(client_socket)
                        return

                if self.receive_event:
                    func, kwargs = self.receive_event

                    func_return = func(data, client_socket, **kwargs)

                    if func_return is not None:
                        self.event_func_return["receive"] = func_return

                self.data = data

        def send(self, client_socket: socket.socket, msg=None):
            """调用该方法，向指定客户端发送消息。若返回值为True，则发送消息成功；若为False则程序异常。

            Arguments:
                client_socket -- 客户端socket。
            """
            
            message = msg if msg else self.reply
            try:
                if self.auto_decode:
                    message = message.encode("utf-8")
                client_socket.sendall(message)
            except socket.error as err:
                self.error_log[datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")] = err
                client_socket.close()
                return False
            else:
                return True

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    
    class RenClient(object):
        """该类为一个客户端类。"""
        
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

            self.main_thread = None
            self.data = None
            self.reply = None
            self.auto_decode = True

            self.prompt_dict = {}
            self.prompt_return_dict = {}

            self.receive_event = ()
            self.conn_event = ()
            self.event_func_return = {}

            self.error_log = {}

        def set_prompt(self, prompt: str | set, func: function, **kwargs):
            """调用该方法，创建一个命令，当服务端发送该命令后执行绑定的函数。名令将作为第一个参数传入函数中。
            
            若函数有返回值，返回值储存在对象的`prompt_return_dict`实例属性中，该属性为一个键为命令，值为命令返回值的字典。

            不定关键字参数为函数参数。

            Arguments:
                prompt -- 命令语句。可为一个字符串或一个集合，若为集合，则集合中所有语句都可触发命令。
                func -- 一个函数。
            """ 

            if isinstance(prompt, set):
                for p in prompt:
                    self.prompt_dict[p] = (func, kwargs)
            else:
                self.prompt_dict[prompt] = (func, kwargs)

        def set_reply(self, reply):
            """调用该方法，当接收到消息时自动回复指定的消息。

            Arguments:
                reply -- 要回复的消息。
            """       

            self.reply = reply

        def set_receive_event(self, func: function, **kwargs):
            """调用该方法，指定当接受到消息时的行为。接收到的数据将作为第一个参数。

            若函数有返回值，则返回值储存在对象的`prompt_return_dict`实例属性中。该事件返回值的键为`receive`。

            不定关键字参数为函数参数。

            Arguments:
                func -- 一个函数。
            """            

            self.receive_event = (func, kwargs)

        def set_conn_event(self, func: function, **kwargs):
            """调用该方法，指定成功连接服务端后的行为。

            若函数有返回值，则返回值储存在对象的`prompt_return_dict`实例属性中。该事件返回值的键为`conn`。

            不定关键字参数为函数参数。

            Arguments:
                func -- 一个函数。
            """            

            self.conn_event = (func, kwargs)

        def run(self):
            """调用该方法，开始尝试连接服务端。"""            

            try:
                self.socket.connect((self.target_ip, self.target_port))
            except socket.error as err:
                self.error_log[datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")] = err
                return

            if self.conn_event:
                func, kwargs = self.conn_event
                func_return = func(**kwargs)

                if func_return is not None:
                    self.event_func_return["conn"] = func_return

            self.main_thread = threading.Thread(target=self._receive)
            self.main_thread.daemon = True
            self.main_thread.start()

            def reboot(self):
                """调用该函数，重新开始通信并清除错误日志。"""

                self.close()
                self.error_log = {}
                self.run()  

        def close(self):
            """调用该方法，关闭客户端。"""

            self.socket.close()     

        def _receive(self):
            """该方法用于创建接收线程，处理接收事件。用于类内部使用，不应被调用。"""
            
            while True:
                try:
                    data = self.socket.recv(self.max_data_size)
                    if self.auto_decode:
                        data = data.decode("utf-8")
                except socket.error as err:
                    self.error_log[datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")] = err
                    return

                if data in self.prompt_dict.keys():
                    func, kwargs = self.prompt_dict[data]
                    func_return = func(data, **kwargs)

                    if func_return is not None:
                        self.prompt_return_dict[data] = func_return

                if self.reply:
                    res = self.send()
                    if not res:
                        return

                if self.receive_event:
                    func, kwargs = self.receive_event

                    func_return = func(data, **kwargs)

                    if func_return is not None:
                        self.event_func_return["receive"] = func_return

                self.data = data

        def send(self, msg=None):
            """调用该方法，向指定客户端发送消息。若返回值为True，则发送消息成功；若为False则程序异常。

            Keyword Arguments:
                msg --要发送的消息。 (default: {None})
            """            
            
            message = msg if msg else self.reply
            try:
                if self.auto_decode:
                    message = message.encode("utf-8")
                self.socket.sendall(message)
            except socket.error as err:
                self.error_log[datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")] = err
                self.socket.close()
                return False
            else:
                return True

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass