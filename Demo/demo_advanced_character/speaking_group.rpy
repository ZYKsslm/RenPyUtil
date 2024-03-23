# 游戏的脚本可置于此文件中。
 
# 先定义一个角色组
default speaking_group = CharacterGroup()

default a = AdvancedCharacter(
    "Alice", 
    image="alice",  # 绑定相应角色的立绘图像标签
    callback=partial(speaking_group.stress, "alice") # 使用partial函数传入自带参数的回调函数。第一个参数为对话组的stress方法，第二个为当前角色立绘的标签名
)

default m = AdvancedCharacter(
    "Mary",
    image="mary",
    callback=partial(speaking_group.stress, "mary")
)

default s = AdvancedCharacter(
    "Sylvie",
    image="sylvie",
    callback=partial(speaking_group.stress, "sylvie")
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
    # 将角色（立绘标签名）加入对话组中
    $ speaking_group.add_characters("alice", "mary", "sylvie")
 
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
    $ speaking_group.del_characters("sylvie")
    hide sylvie

    "Sylvie left."

    m "She has left now."
    a "This is our turn."
 
    return