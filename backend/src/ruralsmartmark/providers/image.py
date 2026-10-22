from io import BytesIO
from typing import Protocol

from PIL import Image, ImageDraw

from ..config import Settings


class ImageProvider(Protocol):
    name: str

    async def generate(self, prompt: str, *, width: int = 1024, height: int = 1024) -> bytes: ...


class MockImageProvider:
    name = "mock"

    async def generate(self, prompt: str, *, width: int = 1024, height: int = 1024) -> bytes:
        image = Image.new("RGB", (width, height), "#F7F3EA")
        draw = ImageDraw.Draw(image)
        draw.rectangle(
            [32, 32, width - 32, height - 32],
            fill="#F7E4DE",
            outline="#B6402A",
            width=6,
        )
        draw.text((56, 56), "MOCK PACKAGING", fill="#1F2A24")
        draw.text((56, 88), "image provider placeholder", fill="#5F655F")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()


class SiliconFlowImageProvider:
    name = "siliconflow"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def generate(self, prompt: str, *, width: int = 1024, height: int = 1024) -> bytes:
        raise NotImplementedError("SiliconFlow image provider lands in Phase 4")


def get_image_provider(_settings: Settings) -> ImageProvider:
    # Phase 0: keep the app fully runnable without an image key.
    return MockImageProvider()
