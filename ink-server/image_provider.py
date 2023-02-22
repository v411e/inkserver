import abc
from typing import Union
from aiohttp import ClientSession
import os, random, logging
from wand.image import Image


class ImageProviderInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return hasattr()

    def __init__(self, root_path: str = "data") -> None:
        self.root_path = root_path

    @abc.abstractmethod
    def get_random_image() -> Union[str, None]:
        """Fetch image from resource, save it as file and return path

        Returns:
            Union[str, None]: Path of saved image-file or None if no image is available
        """
        raise NotImplementedError

    @staticmethod
    def random_provider():
        """Creates and returns an instance of a random type

        Returns:
            _type_: ImageProviderInterface instance
        """
        return random.choice(
            [XKCDImageProvider(root_path="data"), LocalImageProvider(root_path="data")]
        )

    @staticmethod
    def _fits_on_screen(
        img: Union[str, Image],
        screen_width: int = 800,
        screen_heigth: int = 1200,
        max_deviation: int = 0.7,
    ) -> bool:
        """Check whether image is readable on screen of given size

        Args:
            img (Union[str, Image]): The image
            screen_width (int, optional): Width of the screen. Defaults to 800.
            screen_heigth (int, optional): Heigth of the screen. Defaults to 1200.
            max_deviation (int, optional): Maximum deviation from screen aspect ratio if either width or heigth of the image is bigger than the screen. Defaults to 0.7.

        Returns:
            bool: Whether image fits on screen
        """
        sceen_aspect_ratio = screen_width / screen_heigth
        ratio = 1
        if isinstance(img, str):
            with Image(filename=img) as image:
                # If image is smaller than screen, just return True.
                if image.width <= screen_width and image.height <= screen_heigth:
                    return True
                image.auto_orient()
                ratio = image.width / image.height
        if abs(sceen_aspect_ratio - ratio) < max_deviation:
            return True
        else:
            return False

    @staticmethod
    def _edit_image(
        filename: str,
        width: int = 1200,
        height: int = 825,
        format: str = "png",
        crop: bool = True,
        padding: int = 0,
    ) -> str:
        """Edit image to match given height, width and format.

        Args:
            filename (str): Filename or path to the image that should be modified
            width (int, optional): Width of output file. Defaults to 1200.
            height (int, optional): Heigth of output file. Defaults to 800.
            format (str, optional): Format of output file. Defaults to "png".
            crop (bool, optional): Whether image should be cropped. Defaults to True.
            padding (int, optional): Amount of padding that should be applied before extending. Defaults to 0.

        Returns:
            str: Path to the output file.
        """
        with Image(filename=filename) as img:
            img.auto_orient()
            if crop:
                img.transform(resize=f"{width-padding}x{height-padding}^")
            else:
                img.transform(resize=f"{width-padding}x{height-padding}")
            img.extent(width=width, height=height, gravity="center")
            img.format = format
            img.save(filename=f"image.{format}")
        return f"image.{format}"


class XKCDImageProvider(ImageProviderInterface):
    async def get_random_image(self) -> Union[str, None]:
        out_file_name = "xkcd.png"

        # Try multiple times to fetch an image that fits on the screen
        for i in range(10):
            try:
                await self._fetch_from_xkcd(out_file_name)
                if self._fits_on_screen(out_file_name):
                    return self._edit_image(out_file_name, crop=False, padding=5)
            except Exception as e:
                logging.getLogger("ink").error(e)
                return None
        return None

    @staticmethod
    async def _fetch_from_xkcd(out_file_name: str = "xkcd.png"):
        """Fetches a random image from xkcd and saves it as a file

        Args:
            out_file_name (str, optional): Filename for downloaded image. Defaults to "xkcd.png".
        """
        max_num = 1
        img_url = ""

        async with ClientSession() as session:
            async with session.get("https://xkcd.com/info.0.json") as resp:
                print(resp.status)
                json_resp = await resp.json()
                max_num = json_resp.get("num")
            num = random.randrange(1, max_num)
            logging.getLogger("ink").info(f"Fetching xkcd no. {num}")
            async with session.get(f"https://xkcd.com/{num}/info.0.json") as resp:
                print(resp.status)
                json_resp = await resp.json()
                img_url = json_resp.get("img")
            async with session.get(img_url) as resp:
                img = await resp.read()
                with open(out_file_name, "wb") as f:
                    f.write(img)


class LocalImageProvider(ImageProviderInterface):
    async def get_random_image(self) -> Union[str, None]:
        files: list = os.listdir(self.root_path)
        if len(files) > 0:
            return self._edit_image(os.path.join(self.root_path, random.choice(files)))
        else:
            return None
