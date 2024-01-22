# RenPyUtil.resource_preserver 模块测试

# 定义加密器对象
define cryptographer = RenCryptographer(DEBUG=False)    # DEBUG 参数不填默认为 False。开启 DEBUG 将会有控制台输出


image bg:
    "images/bg.png"
    zoom 0.4


label quit:
    # 取消占用资源文件
    scene black with dissolve
    stop music
    # 保证用户退出游戏所有资源文件一定处于加密状态
    $ cryptographer.encrypt_all(regen=True) # regen 参数表示是否使用新的加密器，这样每次进入游戏资源文件的秘钥都将不同
    # 等效语句。一般用于选择加密单个或多个资源文件
    # $ cryptographer.encrypt_archives("images/bg.png", "audio/bgm.mp3", regen=True)
    return

label start:

    # 取消注释下面的语句，加密资源文件以打包游戏，加密成功后须继续注释或删除该语句
    # 共三种模式，请选择其中一项 

    # 通过目录匹配资源文件
    # $ cryptographer.encrypt_files(Finder.get_files_by_dir("images", "audio"))
    # 通过文件类型匹配资源文件
    # $ cryptographer.encrypt_files(Finder.get_files_by_type("png", "jpg", "mp3"))
    # 通过正则表达式（标准）匹配资源文件
    # $ cryptographer.encrypt_files(Finder.get_files_by_re(r''))
    
    "The test will start next."

    # 解密所有资源文件
    $ cryptographer.decrypt_all()
    # $ cryptographer.decrypt_archives("images/bg.png", "audio/bgm.mp3")   等效语句

    scene bg with dissolve
    play music "audio/bgm.mp3" fadein 0.5 fadeout 0.5

    pause

    # 重新加密前须取消占用资源文件
    scene black with dissolve
    stop music

    # 再次加密
    $ cryptographer.encrypt_all(regen=True)

    # python:
    #     # 以上语句的等效语句，但是有 BUG，目前还没解决
    #     with cryptographer(all=True, regen=True):
    #         renpy.show("bg")
    #         renpy.with_statement(dissolve)
    #         renpy.music.play("audio/bgm.mp3")

    #         renpy.pause()

    #         renpy.scene()
    #         renpy.show("black")
    #         renpy.with_statement(dissolve)
    #         renpy.music.stop()

    "The test is over."

    return