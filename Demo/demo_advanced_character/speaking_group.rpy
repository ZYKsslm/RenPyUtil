init python:
    from ren_advanced_character import AdvancedCharacter, SpeakingGroup


default a = AdvancedCharacter(
    "Alice", 
    image="alice",  # 绑定相应角色的立绘图像标签
)

default m = AdvancedCharacter(
    "Mary",
    image="mary",
)

default s = AdvancedCharacter(
    "Sylvie",
    image="sylvie",
)

# 定义一个对话组
default speaking_group = SpeakingGroup(a, m, s)


# 定义角色不同表情的立绘
image alice blush = "images/Alice_VNSpriteSet/Alice_Blush.png"
image alice default = "images/Alice_VNSpriteSet/Alice_Default.png"
image alice worried = "images/Alice_VNSpriteSet/Alice_Worried.png"
image alice doubt = "images/Alice_VNSpriteSet/Alice_Doubt.png"

image mary angry = "images/Sprite - Female Pink Hair Starter Pack/Sprite F PinkH Professional Angry01.png"
image mary smile = "images/Sprite - Female Pink Hair Starter Pack/Sprite F PinkH Professional Smile01.png"

image sylvie smile = "images/Sprite Starter Pack - Female White Hair/FWH smile01.png"
image sylvie angry = "images/Sprite Starter Pack - Female White Hair/FWH angry01.png"


label start:
    # 将角色加入对话组中
    #$ speaking_group.add_characters(a, m, s)

    show alice blush:
        zoom 0.65
        center
    
    a "a"
    a default "a default"

    show mary angry:
        zoom 0.7
        left

    m "m"
    m smile "m smile"

    show sylvie smile:
        zoom 0.65
        right

    s "s"
    s angry "s angry"

    a "return to a"

    m "return to m"

    hide sylvie

    "Sylvie left."

    m "She has left now."
    a "This is our turn."
 
    return
