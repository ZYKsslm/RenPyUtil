define e = Character("艾琳")
define gpt = RenChatGPT(
    api = "https://api.openai.com/v1/models",
    key=None
)

label start:
    while True:
        python:
            content = renpy.input("说点什么")
            gpt.chat(content)

            if not gpt.error:
                # 提取对话
                msgs = gpt.parse_words(gpt.msg)
            else:
                e("[gpt.error!q]")
            
            for msg in msgs:
                e("[msg!q]")