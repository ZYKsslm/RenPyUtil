# 此文件提供了一系列基于Ren'Py的功能类，以供Ren'Py开发者调用
# 作者  ZYKsslm
# 仓库  https://github.com/ZYKsslm/RenPyUtil
# 声明  该源码使用 MIT 协议开源，但若使用需要在程序中标明作者消息


"""renpy
init -1 python:
"""


import re
import json
import requests


class RenChatGPT(object):
    """该类用于Ren'Py兼容地与ChatGPT交互，请求参数必须与官方一致。"""        

    def __init__(self, api, key, dialog=[]):
        """初始化配置。

        Arguments:
            api -- 请求API。
            key -- 用于请求的Key。

        Keyword Arguments:
            dialog -- 一个列表，里面为对话记录。 (default: {None})
        """            

        self.api = api
        self.key = key
        self.dialog = dialog
        self.msg = None
        self.error = None
        self.waiting = False
    
    def chat(self, msg, role="user", model="gpt-3.5-turbo", notice=True, **kwargs):
        """调用该方法，与ChatGPT进行对话，并进行非阻塞式地等待。

        Arguments:
            msg -- 对话内容。

        Keyword Arguments:
            role -- 角色。 (default: {"user"})
            model -- 模型。 (default: {"gpt-3.5-turbo"})
            notice -- 若为True，将在屏幕左上角显示网络请求状态。 (default: {True})

        不定参数`kwargs`为自定义的其他请求参数。
        """

        renpy.invoke_in_thread(self._chat, msg, role, model, notice, **kwargs)
        while self.waiting:
            renpy.pause()

    def _chat(self, msg, role, model, notice, **kwargs):
        self.waiting = True
        if notice:  
            renpy.notify("请求已发送，请稍后......")
        
        headers = {
            "Content-Type": "application/json",
        }

        if self.key:
            headers.update(
                {"Authorization": f"Bearer {self.key}"}
            )

        content = {
            "role": role,
            "content": msg
        }


        self.dialog.append(content)

        data = {
            "model": model,
            "messages": self.dialog
        }

        data.update(kwargs)

        try:
            response = requests.post(self.api, headers=headers, data=json.dumps(data))
            print(response.json())
            message = response.json()["choices"][0]["message"]
            self.msg = message["content"]
            self.dialog.append(message)
        except Exception as e:
            self.msg = None
            self.error = e
            if notice:
                renpy.notify("发生异常，单击继续......")
            self.waiting = False
            return
        
        if notice:
            renpy.notify("接收到回复，单击继续......")
        self.waiting = False
    
    def parse_words(self, text):
        """调用该方法，将段落分成句子。该方法旨在实现更加真实的聊天情景。

        Arguments:
            text -- 文本。

        Returns:
            一个元素为一句话的列表。
        """            
        words = []
        # 判断是否有代码块  # TODO

        # 获取每句话
        res = re.findall(r'(.*?(。|\?|？|!|！|:|：|\.|——))', text)
        for r in res:
            words.append(r[0])
        # 获取最后一个标点后的所有字符
        p = re.compile(fr'{res[len(res)-1][0]}(.*)', flags=re.S)
        last_word = re.findall(p, text)[0]
        if last_word:
            words.append(last_word)

        return words