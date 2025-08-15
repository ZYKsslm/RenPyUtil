import asyncio
import threading

from typing import Callable
from functools import partial

from .logger import get_logger

try:
    import renpy.exports as renpy  # type: ignore
except ImportError:
    IN_RENPY = False
else:
    IN_RENPY = True


logger = get_logger("util")


class Conductor:
    
    @staticmethod
    def invoke_in_thread(func: Callable, *args, **kwargs):
        if IN_RENPY:
            renpy.invoke_in_thread(func, *args, **kwargs) # type: ignore
        else:
            t = threading.Thread(target=func, args=args, kwargs=kwargs)
            t.start()
            return t
    
    @staticmethod
    def on_thread(func: Callable):
        def wrapper(*args, **kwargs):
            if IN_RENPY:
                renpy.invoke_in_thread(func, *args, **kwargs) # type: ignore
            else:
                threading.Thread(target=func, args=args, kwargs=kwargs).start()

        return wrapper
    
    @staticmethod
    async def async_run(func: Callable, *args, **kwargs):
        try:
            if asyncio.iscoroutinefunction(func):
                await func(*args, **kwargs)
            else:
                func(*args, **kwargs)
        except Exception as e:
            logger.error(f"执行回调时发生异常: {e}")


class FakeBlock:
    def __init__(self, block_task: Callable, *args, **kwargs):
        if not IN_RENPY:
            raise RuntimeError("FakeBlock 只能在 Ren'Py 环境中使用")
        
        self.task = partial(block_task, *args, **kwargs)
        self.done = False
        self.result = None

    def _invoke_task(self):
        self.result = self.task()
        self.done = True

    def start(self, conductor: Conductor = Conductor()):
        conductor.invoke_in_thread(self._invoke_task)
        while not self.done:
            renpy.pause(0) # type: ignore
        return self.result
