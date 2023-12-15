init python:
    def conn_suc():
        renpy.notify("连接成功！点击屏幕继续......")
 
    def conn_err(err):
        renpy.notify(f"出现异常：\n{err}")
 
    def receive(msg):
        renpy.notify(f"接收到服务端消息：\n{msg.decode('utf-8')}")
 
 
define e = Character("艾琳")
define client = RenClient("192.168.2.169", 8888, history=True, character=e)
 
screen leave():
    frame:
        align (0.0, 0.0)
        textbutton "返回标题":
            action MainMenu(save=False)
 
# 确保回到标题前关闭连接
label before_main_menu:
    python:
        try:
            if server.has_communicated:
                server.close()
        except:
            pass
    return
 
# 确保退出前关闭连接
label quit:
    python:
        try:
            if server.has_communicated:
                server.close()
        except:
            pass
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
        with client:
            client.set_conn_event(conn_suc)
            client.set_receive_event(receive)
            client.set_error_event(conn_err)
            renpy.notify("开始连接！")
            client.run()
            client.listen_event(RenClient.CONNECT_EVENT, "正在连接中......")
            while True:
                content = renpy.input("说点什么呢？")
                if client.send(Message(content)):
                    renpy.notify("消息发送成功！")