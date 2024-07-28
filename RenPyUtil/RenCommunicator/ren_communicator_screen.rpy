screen ren_communicator_chat(ren_communicator, can_send=False, socket=None):
    zorder 100

    frame:
        align (1.0, gui.textbox_yalign)
        vbox:
            spacing 10
            label "聊天" xalign 0.5 yoffset 10
            null height 10
            if can_send:
                textbutton "发送消息" action ShowMenu("ren_communicator_chat_input", ren_communicator, socket) xalign 0.5
            textbutton "重新连接" action Function(ren_communicator.reboot) xalign 0.5
            textbutton "退出聊天" action Function(ren_communicator.quit_chat) xalign 0.5


screen ren_communicator_chat_input(ren_communicator, socket):
    zorder 100
    default msg = ""

    frame:
        xysize (800, 500)
        align (0.5, 0.5)

        label "请输入消息:" align (0.5, 0.15)

        default msg_value = ScreenVariableInputValue("msg")

        input:
            align (0.5, 0.5)

            multiline True
            copypaste True
            value msg_value
        
        textbutton "完成":
            align (0.5, 0.75) 
            if socket:
                action [Function(ren_communicator.send, socket, Message.string(msg), block=True), Return()]
            else:
                action [Function(ren_communicator.send, Message.string(msg), block=True), Return()]
        
        text "默认输入 shift+enter 换行" align (0.5, 1.0)
