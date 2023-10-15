# 游戏的脚本可置于此文件中。
init python:

    # 定义接收事件的函数
    def receive_im(data):
        save_path = renpy.config.gamedir
        with open(f"{save_path}/images/im.png", "ab") as im:
            im.write(data)


default e = Character("艾琳", who_color="#00CED1")

# 游戏在此开始。

label start:

    e "ren_communicator模块测试。"

    python:
        client = RenClient("192.168.2.93", 8888, max_data_size=4096) 
        client.auto_decode = False  # 由于接收的是图片而不是字符串，所以不用自动转换。
        client.set_receive_event(
            func=receive_im
        )
        client.run()    # 这一行主线程会被阻塞，即卡住直到成功连接主机或引发超时报错。

    e "你想看哪张图片？"
    menu:
        # 将图片名称发送给服务端
        "第一张":
            $ client.send("im1".encode("utf-8"))    # 字符串的encode()方法可以手动把字符串转换成字节流。
        "第二张":
            $ client.send("im2".encode("utf-8"))
        "第三张":
            $ client.send("im3".encode("utf-8"))
        "第四张":
            $ client.send("im4".encode("utf-8"))

    # 阻塞主线程。
    pause

    $ client.close()   # 由于回到主菜单通信依然存在，所以需要手动关闭所有连接。

    return