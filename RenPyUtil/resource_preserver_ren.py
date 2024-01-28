# 此文件提供了一系列基于Ren'Py的功能类，以供Ren'Py开发者调用
# 作者  ZYKsslm
# 仓库  https://github.com/ZYKsslm/RenPyUtil
# 声明  该源码使用 MIT 协议开源，但若使用需要在程序中标明作者消息


"""renpy
python early:
"""


import os
import re
import pickle
from contextlib import contextmanager

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


class Finder(object):
    """文件及路径操作。"""
    
    @staticmethod
    def parse_path(*renpy_paths):
        """调用该静态方法，把renpy路径转换为绝对路径。
        
        Returns:
            一个绝对路径。
        """
        
        path = os.path.join(config.gamedir, *renpy_paths)
        path = re.sub(r"\\", "/", path)
        
        return path

    @staticmethod
    def get_files_by_type(*tps):
        """调用该方法，返回指定类型的文件。

        将在`game`目录下查找文件。
        """        
        
        base_path = Finder.parse_path()
        all_files = [file for file in os.walk(base_path)]
        
        abs_files = []
        for files in all_files:
            base = files[0]
            sub = files[2]
            paths = [re.sub(r"\\", "/", os.path.join(base, p)) for p in sub]
            
            abs_files += paths
        
        files = []
        for file in abs_files:
            file_tp = os.path.splitext(file)[1].replace(".", "")
            for tp in tps:
                if tp == file_tp:
                    files.append(file)
                    
        return files
    
    @staticmethod
    def get_files_by_re(*re_strs: str):
        """调用该方法，返回正则表达式匹配到的文件。

        将在`game`目录下查找文件。
        """
        
        patterns = [re.compile(re_str) for re_str in re_strs]
        base_path = Finder.parse_path()
        all_files = [file for file in os.walk(base_path)]
        
        abs_files = []
        for files in all_files:
            base = files[0]
            sub = files[2]
            paths = [re.sub(r"\\", "/", os.path.join(base, p)) for p in sub]
            
            abs_files += paths
        
        files = []
        for file in abs_files:
            matches = [re.search(pattern, file) for pattern in patterns]
            for match in matches:
                if match:
                    files.append(match.group())
        
        return files
    
    @staticmethod
    def get_files_by_dir(*dirs):
        """调用该方法，返回指定目录下文件。应为renpy路径。

        将在`game`目录下查找文件。
        """
        
        all_files = [os.walk(Finder.parse_path(dir)) for dir in dirs]
        
        abs_files = []
        for files in all_files:
            for file in files:
                paths = [re.sub(r"\\", "/", os.path.join(file[0], p)) for p in file[2]]
            
                abs_files += paths

        return abs_files
        

class Resource(object):
    """资源类，用于保存每一个资源文件的状态及加密信息。
    
    所有资源在退出程序时应始终保持加密即`ENCRYPTED`状态。
    """    
    
    ENCRYPTED = 0
    
    DECRYPTED = 1
    
    def __init__(self, file: str, cipher: dict[str, bytes] = {}, position: tuple[int, int] = (0, 0)):
        """初始化方法。

        Arguments:
            file -- 资源文件，应为renpy路径。
        
        Keyword Arguments:
            cipher -- 应为一个储存了加密信息的字典。 (default: {{}})
            position -- 资源在归档文件中的位置。 (default: {(0, 0)})
        """        
        
        self.file = file
        self.position = position
        self.cipher = cipher
        self.state = Resource.ENCRYPTED
        
    def encrypt(self):
        """加密资源文件后应该调用该方法。"""
        
        if self.state == Resource.ENCRYPTED:
            raise Exception(f"{self.file}已处于密文状态！")
        else:
            self.state = Resource.ENCRYPTED
        
    def decrypt(self):
        """解密资源文件后应该调用该方法。"""
        
        if self.state == Resource.DECRYPTED:
            raise Exception(f"{self.file}已处于明文状态！") 
        else:
            self.state = Resource.DECRYPTED 
    
    def get_cipher(self):
        """调用该方法，返回自身的加密器。"""        

        return AES.new(self.cipher["key"], AES.MODE_CBC, self.cipher["iv"])


class RenCryptographer(object):
    """资源加密器。用于操作资源和加密器状态。"""    
    
    def __init__(self, DEBUG=False):
        """初始化方法。

        Keyword Arguments:
            DEBUG -- 是否开启DEBUG模式，若是则加密器活动将在控制台输出。 (default: {False})
        """          
    
        self.resources: dict[str, Resource] = {}
        self.latest_files: list[str] = []
        self.context_mode = {
            "files": (),
            "kwargs": {}
        }
        self.DEBUG = DEBUG
        self.ENCRYPT_MODE = False
        
        self.load_cipher()
    
    def load_cipher(self):
        """调用该方法，加载加密器信息初始化密码器。"""        
        
        if not os.path.exists(Finder.parse_path("archive.rpa")):
            return 
        
        with open(Finder.parse_path("data"), "rb") as r:  
            self.resources: dict[str, Resource] = pickle.load(r)
            
            for resource in self.resources.values():
                position: tuple[int, int] = resource.position
                if position[0] == 0 and position[1] == 0:
                    p: tuple[int, int, bytes] = renpy.loader.archives[0][1][resource.file][0]
                    resource.position = (p[0], p[1])
        
        if self.DEBUG:
            # DEBUG   
            print("本地加密器已加载。")
            for file, resource in self.resources.items():
                print(file)
                print(f"key:{resource.cipher['key']}")
                print(f"iv:{resource.cipher['iv']}")
    
    def decrypt_archives(self, *files):
        """调用该方法，解密归档文件中的资源文件。""" 
        
        if not self.resources:
            return
        
        if self.ENCRYPT_MODE:
            return
        
        if not files:
            files = self.latest_files
        
        self.latest_files.clear()
        for file in files:
            if (resource := self.resources[file]).state == Resource.DECRYPTED:
                continue
            
            offset = resource.position[0]
            length = resource.position[1]

            try:
                with open(Finder.parse_path("archive.rpa"), "rb+") as arc:
                    arc.seek(offset)
                    ciphertext = arc.read(length)
                    plaintext = resource.get_cipher().decrypt(ciphertext)
                    arc.seek(offset)
                    arc.write(plaintext)
                    resource.decrypt()
                
                if self.DEBUG:
                    # DEBUG
                    print(f"{file}已解密")
                    print(f"key:{resource.cipher['key']}")
                    print(f"iv:{resource.cipher['iv']}")
                
            except PermissionError:
                self.decrypt_archives(*files)

            self.latest_files.append(file)
    
    def encrypt_archives(self, *files, regen=False):
        """调用该方法，加密归档文件中的资源文件。

        不定参数为资源文件的renpy路径。
        
        不定关键字参数`regen`若为`True`则使用新的加密器，默认为`False`。
        """          
        
        if not self.resources:
            return
        
        if self.ENCRYPT_MODE:
            return 
        
        if not files:
            files = self.latest_files
        
        renpy.pause(0.05)
        self.latest_files.clear()
        for file in files:
            if (resource := self.resources[file]).state == Resource.ENCRYPTED:
                continue
            
            if regen:
                key = get_random_bytes(32)
                iv = get_random_bytes(16)
                cipher = AES.new(key, AES.MODE_CBC, iv)
                resource.cipher = {
                    "key": key,
                    "iv": iv
                }
            else:
                cipher = resource.get_cipher()
            
            offset = resource.position[0]
            length = resource.position[1]
            
            try:
                with open(Finder.parse_path("archive.rpa"), "rb+") as arc:
                    arc.seek(offset)
                    plaintext = arc.read(length)
                    ciphertext = cipher.encrypt(plaintext)
                    arc.seek(offset)
                    arc.write(ciphertext)
                    resource.encrypt()
                
                if self.DEBUG:
                    # DEBUG
                    if regen:
                        print(f"{file}已使用新的加密器加密")
                    else:
                        print(f"{file}已重新加密")
                    print(f"key:{resource.cipher['key']}")
                    print(f"iv:{resource.cipher['iv']}")
                
            except PermissionError:       
                self.encrypt_archives(*files, regen=regen)   
            finally:
                self.save_cipher() 
                
            self.latest_files.append(file)
            
    def decrypt_all(self):
        """调用该方法，解密归档文件中所有处于密文状态的资源文件。
        
        当资源文件数量过多时，可能造成卡顿。
        """
        
        self.decrypt_archives(*self.resources.keys())        
    
    def encrypt_all(self, regen=False):
        """调用该方法，加密归档文件中所有处于明文状态的资源文件。
        
        当资源文件数量很多时，可能造成卡顿。

        Keyword Arguments:
            regen -- 是否使用新的加密器。 (default: {False})
        """           
        
        self.encrypt_archives(*self.resources.keys(), regen=regen)
    
    def save_cipher(self):
        """调用该方法，保存加密器以下次启动游戏使用。
        
        该方法一般在使用新加密器加密资源文件后调用。
        """  
        
        with open(Finder.parse_path("data"), "wb") as r:
            pickle.dump(self.resources, r)      
        
        if self.DEBUG:
            # DEBUG
            print("当前加密器已保存至本地。")
            for file, resource in self.resources.items():
                print(file)
                print(f"key:{resource.cipher['key']}")
                print(f"iv:{resource.cipher['iv']}")
    
    # TODO: 上下文管理器
    # renpy特性 BUG
    
    # 上下文管理器协议实现
    def __call__(self, *files, **kwargs):
        self.context_mode["files"] = files
        self.context_mode["kwargs"] = kwargs
        return self
    
    def __enter__(self):
        if "all" in self.context_mode["kwargs"] and self.context_mode["kwargs"]["all"] is True:
            self.decrypt_all()
        else:
            self.decrypt_archives(*self.context_mode["files"])
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if "all" in self.context_mode["kwargs"] and self.context_mode["kwargs"]["all"] is True:
            self.encrypt_all(**self.context_mode["kwargs"])
        else:
            self.encrypt_archives(*self.context_mode["files"], **self.context_mode["kwargs"])
    
    # 方法实现
    @contextmanager
    def release(self, *files, **kwargs):
        """该方法实现了一个上下文管理器，允许暂时释放即自动加解密资源文件。

        不定参数为需要释放的资源文件，应为renpy路径。
        
        该方法因renpy特性原因可能造成BUG。

        Yields:
            一个`RenCryptographer`对象，即本身。
        """        
        
        try:
            self.decrypt_archives(*files)
            yield self
        except Exception:
            return
        else:
            self.encrypt_archives(*files, **kwargs)
    
    @contextmanager
    def release_all(self):
        """该方法实现了一个上下文管理器，允许暂时释放所有资源文件。

        该方法因renpy特性原因可能造成BUG。
        
        Yields:
            一个`RenCryptographer`对象，即本身。
        """   
        
        try:
            self.decrypt_all()
            yield self
        except Exception:
            return
        else:
            self.encrypt_all()

    def encrypt_files(self, files: list, guide=True):
        """调用该函数，使用随机秘钥加密文件。
        
        使用 AES-256 加密算法 CBC 模式。

        Arguments:
            files -- 要加密的文件列表。

        Keyword Arguments:
            guide -- 是否开启指引。 (default: {True})

        Raises:
            Exception: 未匹配到文件。
        """        
        
        self.ENCRYPT_MODE = True
        
        if guide:
            renpy.say("ZYKsslm", "接下来将进行资源文件加密，此过程当前通常不可逆，请先保证程序能够正常退出！\n准备好则请点击任意处开始加密。")

        resources = {}
        
        if not files:
            raise Exception("未匹配到任何文件，无法加密！")
        
        for file in files:
            
            with open(file, "rb") as f:
                plaintext = f.read()
                
                if (length := len(plaintext)) % 16 != 0:
                    plaintext += b' ' * (16 - length % 16)  # 填充数据至 16 的倍数长度
                
                key = get_random_bytes(32)
                iv = get_random_bytes(16)
                cipher = AES.new(key, AES.MODE_CBC, iv)
                ciphertext = cipher.encrypt(plaintext)
                
            with open(file, "wb") as f:
                f.write(ciphertext)

            cipher = {
                "key": key,
                "iv": iv
            }

            file_name = file.replace(Finder.parse_path() + "/", "")
            resources[file_name] = Resource(file_name, cipher)
        
        with open(Finder.parse_path("data"), "wb") as d:
            pickle.dump(resources, d)
        
        if guide:
            renpy.say("ZYKsslm", "资源文件加密成功，请点击右上角正常退出游戏，删除或注释调用了 encrypt_files() 函数的语句！\n并将加密过的资源文件打包进归档文件即 archive.rpa 中。")