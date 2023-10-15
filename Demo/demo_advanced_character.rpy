# 游戏的脚本可置于此文件中。
init python:
 
 
    # 一个任务函数，该函数的参数必须为一个字典
    def love(speaker, name):
 
        renpy.say(speaker, fr"{name}, I love you.")
        recieve = renpy.input("So, your answer is......")
 
        return recieve
 
 
# 使用default语句定义高级角色对象
default e = AdvancedCharacter("艾琳", what_color="#FF8C00", who_color="#00CED1")
 
 
# 游戏在此开始。
 
label start:
 
    python:
        # 两种给高级角色增添属性的写法
        e.add_attr(love_point=50)
        e.add_attr({"strength": 100})
 
    # 输出角色所有的自定义属性及其值
    e "[e.customized_attr_dict!q]"
 
    python:
 
        # 给该角色创建一个任务并绑定一个任务函数，当该角色对象的自定义属性love_point的值达到100时执行任务函数love
        e.set_task(
            task_name="love_task",
            attr_pattern={
                "love_point": 100
            },
            func=love,
            speaker=e,  # 传入函数的参数
            name="Tom"
        )
 
        e.love_point += 50
 
        # 获取任务函数返回值
        recieve = e.task_return_dict["love_task"][0]
     
    e "Your answer is '[recieve!q]'"
 
    return