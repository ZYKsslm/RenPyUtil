# 游戏的脚本可置于此文件中。
 
# 先定义一个角色组
default speanking_group = CharacterGroup()

default a = AdvancedCharacter(
    "Alice", 
    image="alice",  # 绑定相应角色的立绘图像标签
    callback=partial(speanking_group.stress, "a") # 使用partial函数传入自带参数的回调函数。第一个参数为对话组的stress方法，第二个为当前角色对象的变量名
)

default m = AdvancedCharacter(
    "Mary",
    image="mary",
    callback=partial(speanking_group.stress, "m")
)

default s = AdvancedCharacter(
    "Sylvie",
    image="sylvie",
    callback=partial(speanking_group.stress, "s")
)


# 定义角色不同表情的立绘
image alice blush = "images/Alice_VNSpriteSet/Alice_Blush.png"
image alice default = "images/Alice_VNSpriteSet/Alice_Default.png"
image alice worried = "images/Alice_VNSpriteSet/Alice_Worried.png"
image alice doubt = "images/Alice_VNSpriteSet/Alice_Doubt.png"

image mary angry = "images/Sprite - Female Pink Hair Starter Pack/Sprite F PinkH Professional Angry01.png"
image mary smile = "images/Sprite - Female Pink Hair Starter Pack/Sprite F PinkH Professional Smile01.png"

image sylvie smile = "images/Sprite Starter Pack - Female White Hair/FWH smile01.png"
image sylvie angry = "images/Sprite Starter Pack - Female White Hair/FWH angry01.png"

# 游戏在此开始。
 
label start:
    # 将角色对象加入对话组中
    $ speanking_group.add_characters("a", "m", "s")
 
    show alice blush:
        zoom 0.65
        center
    
    a "a"
    a @ default "a default"

    show mary angry:
        zoom 0.7
        left

    m "m"
    m @ smile "m smile"

    show sylvie smile:
        zoom 0.65
        right

    s "s"
    s @ angry "s angry"

    a "return to a"

    m "return to m"

    # 当需要移除角色时（一位角色离场）
    $ speaking_group.del_characters("s")
    hide sylvie

    "Sylvie left."

    m "She has left now."
    s "This is our turn."
 
    return