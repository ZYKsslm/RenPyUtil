# 描述：优化日志，支持异步和文件轮转
# 作者：ZYKsslm
# 仓库：https://github.com/ZYKsslm/RenPyUtil
# 声明：MIT协议开源，需标明作者


import os
import logging
import logging.handlers
import queue

try:
    import renpy.config as config  # type: ignore
    basedir = config.basedir
except ImportError:
    basedir = os.getcwd()


def get_logger(logger_name: str):

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s")

    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    # 文件轮转
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(basedir, "ren_communicator.log"),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # 异步日志队列
    log_queue = queue.Queue()
    queue_handler = logging.handlers.QueueHandler(log_queue)
    queue_listener = logging.handlers.QueueListener(log_queue, console_handler, file_handler)
    queue_listener.start()
    
    logger.addHandler(queue_handler)

    return logger