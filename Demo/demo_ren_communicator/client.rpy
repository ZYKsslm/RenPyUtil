init python:

    client = RenClient("192.168.2.23", 8888)

    @client.on_conn()
    def conn_handler(client):
        renpy.notify("连接成功")

    @client.on_disconn()
    def disconn_handler(client):
        renpy.notify("连接断开")

define s = Character("server")

label start:

    python:
        with client:
            for msg in client.get_message():
                s(msg.get_message())

    return
