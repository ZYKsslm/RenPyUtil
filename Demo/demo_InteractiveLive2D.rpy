define mao = InteractiveLive2D(
    "mtn_01", 
    eye_follow=True,    # 开启眼部跟随
    eye_center=(372, 268),
    head_follow=True,    # 开启头部跟随
    head_center=(372, 268),
    body_follow=True,    # 开启身体跟随
    body_center=(365, 495),
    range=(0, 0, 700, 700),
    filename="live2d/mao_pro",
    loop=True,
    seamless=True
)


screen live2d():
    add mao


label start:

    show expression renpy
    ## 使用界面
    # show screen live2d()
    pause

    return