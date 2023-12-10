# 游戏的脚本可置于此文件中。
 
# 先定义一个角色组
default group = CharacterGroup()
default a = AdvancedCharacter(
    "Alice", 
    what_color="#FF8C00", 
    who_color="#d982e0", 
    image="alice",  # 绑定相应角色的立绘图像标签
    callback=partial(group.stress, "a") # 使用partial函数传入自带参数的回调函数。第一个参数为group.stress函数，第二个为当前角色对象的变量名
)

default s = AdvancedCharacter(
    "S", 
    what_color="#FF8C00", 
    who_color="#d982e0", 
    image="s", 
    callback=partial(group.stress, "s")
)

$ group.add_characters(a, s)    # 将角色加入角色组中

image alice blush = "images/Alice_VNSpriteSet/Alice_Blush.png"
image alice default = "images/Alice_VNSpriteSet/Alice_Default.png"
image alice worried = "images/Alice_VNSpriteSet/Alice_Worried.png"

image s de = "images/Alice_VNSpriteSet/Alice_Teasing.png"
image s em = "images/Alice_VNSpriteSet/Alice_Embarrassed.png"

# 游戏在此开始。
 
label start:
 
    show alice blush:
        zoom 0.6
        center
    a "你好！"

    a default "我是Alice"

    a @ worried "哎呀！ " with hpunch

    a "说什么好呢？"
    
    show s de:
        zoom 0.6
        left
    s "嗨嗨！"

    s em "你好"

    a "你好......"
 
    return