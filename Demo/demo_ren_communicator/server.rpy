init python:
    def conn_suc(socket):
        renpy.notify("连接成功！点击屏幕继续......")
 
    def conn_err(err):
        renpy.notify(f"出现异常：\n{err}")
 
    def receive(msg, socket):
        renpy.notify(f"接收到{socket.getpeername()[0]}的消息：\n{msg.decode('utf-8')}")
 
 
define e = Character("艾琳")
define server = RenServer()
 
screen leave():
    frame:
        align (0.0, 0.0)
        textbutton "返回标题":
            action MainMenu(save=False)
 
# 确保回到标题前关闭连接
label before_main_menu:
    if server.has_communicated:
        $ server.close()
    return
 
# 确保退出前关闭连接
label quit:
    if server.has_communicated:
        $ server.close()
    return
 
 
label start:
 
    e "请愉快地聊天吧！"
    menu:
        "继续":
            jump chat
        "算了":
            return
  
    return
 
label chat:
    show screen leave()
    python:
        with server:
            server.set_conn_event(conn_suc)
            server.set_receive_event(receive)
            server.set_error_event(conn_err)
            renpy.notify("开始连接！")
            server.run()
            server.listen_event(RenServer.CONNECT_EVENT, "正在连接中......")
            while True:
                content = renpy.input("说点什么呢？")
                for socket in server.client_socket_list:
                    if server.send(socket, content.encode("utf-8")):
                        renpy.notify("消息发送成功！")