# 游戏的脚本可置于此文件中。
init python:

    # 定义命令函数。前两个参数是自动传入的，所以自定义参数从第三个开始定义
    def send_im(prompt, socket: socket.socket, server: RenServer):
        server.auto_decode = False  # 由于需要发送图片而不是字符串，所以不用自动转换。
        im_path = renpy.config.gamedir
        path = f"{im_path}/images/{prompt}.png"

        with open(path, "rb") as img:
            server.send(socket, img.read()) # 把图片数据发送给客户端


default e = Character("艾琳", who_color="#00CED1")

# 游戏在此开始。

label start:
    
    e "ren_communicator模块测试。"
    python:
        with RenServer(max_data_size=4096) as server:
            # 设置命令
            server.set_prompt(
                prompt={"im1", "im2", "im3", "im4"},
                func=send_im,
                server=server
            )
            server.run()

    # 阻塞主线程，这时通信线程在运行。
    pause

    $ server.close()   # 由于回到主菜单通信线程依然存在，所以需要手动关闭所有连接。
    $ server.close_all_conn()

    e "[server.error_log!q]"    # 打印错误日志，若无则为空字典。

    return



