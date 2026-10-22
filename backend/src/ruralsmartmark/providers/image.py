from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path
from typing import Protocol

import httpx
from PIL import Image, ImageDraw

from ..config import Settings


class ImageGenerationError(RuntimeError):
    """The image provider returned an error or an unusable payload."""


def select_image_size(width: int, height: int, override: str = "") -> str:
    if override.strip():
        return override.strip()
    if abs(width - height) <= 32:
        return "512x512"
    return "1024x576" if width > height else "768x1024"


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

    def _cache_path(self, prompt: str, size: str) -> Path:
        raw = f"{self._settings.image_model}|{prompt}|{size}|{self._settings.image_negative_prompt}"
        key = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return self._settings.image_cache_path / f"{key}.png"

    async def generate(self, prompt: str, *, width: int = 1024, height: int = 1024) -> bytes:
        cleaned = prompt.strip()
        if not cleaned:
            raise ImageGenerationError("图像 prompt 为空")
        size = select_image_size(width, height, self._settings.image_size)
        cache_path = self._cache_path(cleaned, size)
        if cache_path.is_file():
            return cache_path.read_bytes()

        payload: dict[str, object] = {
            "model": self._settings.image_model,
            "prompt": cleaned,
            "image_size": size,
        }
        if self._settings.image_negative_prompt.strip():
            payload["negative_prompt"] = self._settings.image_negative_prompt.strip()

        headers = {"Authorization": f"Bearer {self._settings.openai_api_key}"}
        async with httpx.AsyncClient(
            timeout=self._settings.image_timeout_seconds,
            follow_redirects=True,
        ) as client:
            response = await client.post(
                f"{self._settings.resolved_image_base_url}/images/generations",
                headers=headers,
                json=payload,
            )
            if response.status_code != 200:
                raise ImageGenerationError(
                    f"生图接口返回 {response.status_code}: {response.text[:300]}"
                )
            try:
                data = response.json()
                first = (data.get("images") or data.get("data") or [])[0]
                url = first.get("url") if isinstance(first, dict) else first
            except (ValueError, IndexError, AttributeError) as exc:
                raise ImageGenerationError("生图接口返回格式无法解析") from exc
            if not url:
                raise ImageGenerationError("生图接口没有返回图片 URL")

            image_response = await client.get(url)
            if image_response.status_code != 200:
                raise ImageGenerationError(
                    f"下载生成图失败 {image_response.status_code}: {image_response.text[:200]}"
                )

        try:
            image = Image.open(BytesIO(image_response.content))
            image.load()
        except OSError as exc:
            raise ImageGenerationError("生图接口返回的文件不是有效图片") from exc

        buffer = BytesIO()
        image.convert("RGB").save(buffer, format="PNG", optimize=True)
        content = buffer.getvalue()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(content)
        return content


def get_image_provider(settings: Settings) -> ImageProvider:
    if not settings.openai_api_key or not settings.image_model.strip():
        return MockImageProvider()
    return SiliconFlowImageProvider(settings)
