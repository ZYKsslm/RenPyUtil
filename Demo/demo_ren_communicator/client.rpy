init python:
 
    def conn_suc():
        renpy.notify("连接成功")
 
    def error(e):
        renpy.notify(e)
 
    def get_im(data):
        with open(f"{renpy.config.gamedir}/images/image.png", "wb+") as f:
            f.write(data)
 
        renpy.notify("图片保存成功！")
 
 
default e = Character("艾琳", who_color="#00CED1")
 
 
label start:
 
    e "ren_communicator模块测试。"
 
    python:
        # 使用with语句可防止用户回滚导致重复发送消息
        with RenClient("192.168.2.23", 8888, max_data_size=5242880) as client:
            client.set_conn_event(conn_suc)
            client.set_receive_event(get_im)
            client.set_error_event(error)
            client.run()
 
            client.listen_event(RenClient.CONNECT_EVENT, "正在等待连接......")
 
    e  "你想看哪一张图片？"
    menu:
        "第一张":
            $ im = "im1"
        "第二张":
            $ im = "im2"
        "第三张":
            $ im = "im3"
        "第四张":
            $ im = "im4"
 
    python:
        with client:
            res = client.send(im.encode("utf-8"))
            client.listen_event(RenClient.CONNECT_EVENT, "正在接收图片......")
     
    e "错误日志：\n[client.error_log!q]"
 
    return