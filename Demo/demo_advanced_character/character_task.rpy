# 游戏的脚本可置于此文件中。
init python:
 
 
    # 一个任务函数
    def love_event(speaker, name):
 
        speaker(f"{name}, I love you.")
        recieve = renpy.input("So, your answer is......")
 
        return recieve
    

    # 使用threading_task装饰的函数将在子线程中运行
    @threading_task
    def thread_event():
        renpy.notify("Messages")
 
 
# 使用default语句定义高级角色对象
default e = AdvancedCharacter("艾琳", what_color="#FF8C00", who_color="#00CED1")
 
 
# 游戏在此开始。
 
label start:
 
    python:
        # 两种给高级角色增添属性的写法
        e.add_attr(love_point=50)
        e.add_attr(thread=False)
        e.add_attr({"strength": 100, "health": 40})
 
    # 输出角色所有的自定义属性及其值
    e "[e.customized_attr_dict!q]"
 
    python:
 
        # 创建一个角色任务
        love_task = CharacterTask(
            attr_pattern={
                "love_point": 100,
                "health": 50
            },
            single_use=True # single_use参数若为True则该任务为一次性任务
        )
        thread_task = CharacterTask(
            attr_pattern={
                "thread": True
            }
        )

        # 绑定任务函数
        love_task.add_func(love_event, e, name="ZYKsslm")
        thread_task.add_func(thread_event)

        # 绑定角色任务
        e.add_task(love_task)
        e.add_task(thread_task)
 
        e.love_point += 50
        e.health += 10

        e.thread=True
 
        # 获取任务函数返回值
        recieve = love_task.func_return["love_event"]
     
    e "Your answer is '[recieve!q]'"
 
    return