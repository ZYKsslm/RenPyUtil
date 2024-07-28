init python:

    server = RenServer()

    @server.on_conn()
    def conn_handler(server, client_name, client_socket):
        renpy.notify(f"{client_name} 已连接")

    @server.on_disconn()
    def disconn_handler(server, client_name):
        renpy.notify(f"{client_name} 已断开连接")


define f = Character("friend")


label start:

    python:
        with server:
            for client_socket, msg in server.get_message():
                f(msg.get_message())
    
    return