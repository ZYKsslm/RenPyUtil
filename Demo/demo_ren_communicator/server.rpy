init python:
 
    # 连接成功后执行的函数
    def conn_suc(socket):
        renpy.notify(f"{socket.getpeername()}已连接")
 
    # 接收到命令后执行的函数
    def get_im(prompt, socket, server):
        renpy.notify("开始发送图片")
 
        path = f"{renpy.config.gamedir}/images/{prompt.decode('utf-8')}.png"
        with open(path, "rb") as f:
            if not server.send(socket, f.read()):
                renpy.notify("发送失败！")
 
        renpy.notify("发送成功！")
 
define e = Character("艾琳")
 
 
label start:
 
    e "ren_communicator模块测试。"
    python:
        # 使用with语句防止用户回滚导致重复创建启动线程
        with RenServer(max_data_size=5242880) as server:    # 5242880B相当于5MB
            server.run()
            # 创建命令对象
            im_prompt = Prompt(
                True,
                "im1",
                "im2",
                "im3",
                "im4"
            )
            # 创建命令任务
            server.set_prompt(im_prompt, get_im, server=server)
            # 创建成功连接后的任务
            server.set_conn_event(conn_suc)
            # 监听连接事件
            server.listen_event(RenServer.CONNECT_EVENT, "正在等待连接......")
            # 监听该命令事件
            server.listen_event(RenServer.PROMPT_EVENT, "等待中......", im_prompt)
  
    e "错误日志：\n[server.error_log!q]"   # 打印错误日志，若无则为空字典。
  
    return