"""renpy
python early:
"""

import logging
import requests
import renpy.exports as renpy  # type: ignore
import renpy.config as config  # type: ignore
from renpy.display.im import Data  # type: ignore
from renpy.defaultstore import Transform  # type: ignore

from pathlib import Path
from hashlib import md5

if not (renpy.windows or renpy.linux):
    import appdirs

logger = logging.getLogger("NetImage")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("[NetImage] %(levelname)s: %(message)s"))
    logger.addHandler(handler)


class NetImage(renpy.Displayable):

    CACHE_DIR = Path(
        config.gamedir if renpy.windows or renpy.linux
        else appdirs.user_data_dir(appname=config.name) # type: ignore
    ) / "net_image_cache"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    CACHED_IMAGES = set(p.stem for p in CACHE_DIR.iterdir() if p.is_file())
    ALL_NET_IMAGES: set["NetImage"] = set()

    def __init__(self, url: str, headers=None, cover=None, **properties):
        """
        :param url: 图片 URL
        :param headers: 可选请求头
        :param cover: 默认白色封面（当图片未加载或加载失败时显示）
        """

        super().__init__(**properties)

        self.url = url
        self.headers = headers or {}
        self.fmt = Path(url).suffix.lower()
        self.cover = renpy.displayable(cover) if cover else renpy.displayable("#ffffff")
        self.md5 = md5(url.encode()).hexdigest()
        self.cache_path = self.CACHE_DIR / f"{self.md5}{self.fmt}"
        self.image = self._load_cache()

        self.ALL_NET_IMAGES.add(self)

    def load_image(self):
        def _task():
            try:
                logger.debug("下载图片: %s", self.url)
                response = requests.get(self.url, headers=self.headers, timeout=30)
                response.raise_for_status()
                self.cache_path.write_bytes(response.content)
                self.CACHED_IMAGES.add(self.md5)
                logger.info("图片已缓存: %s", self.cache_path.name)
                self.image = renpy.displayable((Data(response.content, self.fmt)))
            except Exception as e:
                logger.error("下载失败 [%s]: %s", self.url, e)
            finally:
                renpy.redraw(self, 0)
                renpy.restart_interaction()

        renpy.invoke_in_thread(_task)

    @classmethod
    def preload_all(cls):
        for net_image in cls.ALL_NET_IMAGES:
            if net_image.md5 not in cls.CACHED_IMAGES:
                net_image.load_image()

    def render(self, width, height, st, at):
        render = renpy.Render(width, height)
        render.blit(renpy.render(self.image, width, height, st, at), (0, 0))
        return render

    def _get_image(self):
        if renpy.windows or renpy.linux:
            return self.cache_path.relative_to(config.gamedir).as_posix()
        return Data(self.cache_path.read_bytes(), self.cache_path.name)

    def _load_cache(self):
        if not self.cache_path.exists():
            return self.cover
        return renpy.displayable(self._get_image())

    def __eq__(self, other):
        return isinstance(other, NetImage) and self.url == other.url

    def __hash__(self):
        return hash(self.url)