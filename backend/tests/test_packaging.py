from io import BytesIO
from pathlib import Path

from PIL import Image
from sqlalchemy import select

from ruralsmartmark.models import Batch, ProductProfile
from ruralsmartmark.seed import seed_demo
from ruralsmartmark.services.packaging import (
    BUNDLED_FONTS,
    _font,
    render_label_png_bytes,
)


def test_bundled_fonts_exist_and_are_selected():
    for path in BUNDLED_FONTS.values():
        assert path.exists()
        assert path.stat().st_size > 1_000_000

    sans = _font(20)
    serif_bold = _font(20, serif=True, bold=True)
    assert Path(str(sans.path)).name == "NotoSansSC-Regular.otf"
    assert Path(str(serif_bold.path)).name == "NotoSerifSC-Bold.otf"


async def test_render_png_uses_bundled_fonts(session):
    await seed_demo(session)
    product = await session.scalar(
        select(ProductProfile).where(ProductProfile.slug == "zhaotong-ugly-apple")
    )
    batch = await session.scalar(select(Batch).where(Batch.code == "ZT-2026-001"))
    output = {
        "concept": "牛皮纸礼盒",
        "palette": ["#B6402A", "#C9A46A", "#3F6B4F", "#F7F3EA"],
        "packaging_copy": {
            "front": "丑得真实，甜得直接",
            "back": "来自昭通昭阳区的高海拔果园。",
            "side": "5kg · 12 枚 · 80–85mm",
            "inside": "长得丑，是它认真晒太阳的证据。",
        },
        "structure": {
            "box_type": "牛皮纸天地盖礼盒",
            "dimensions": "360×260×90mm",
            "material": "350g 牛皮纸 + 瓦楞内托",
        },
    }

    data = render_label_png_bytes(
        output,
        batch,
        product,
        public_base_url="http://127.0.0.1:5173",
    )
    image = Image.open(BytesIO(data))

    assert image.format == "PNG"
    assert image.size == (1600, 1000)
    assert len(data) > 50_000


async def test_render_png_handles_multiline_copy(session):
    await seed_demo(session)
    product = await session.scalar(
        select(ProductProfile).where(ProductProfile.slug == "zhaotong-ugly-apple")
    )
    batch = await session.scalar(select(Batch).where(Batch.code == "ZT-2026-001"))
    output = {
        "concept": "牛皮纸礼盒\n克制一点",
        "palette": ["#B6402A", "#C9A46A", "#3F6B4F", "#F7F3EA"],
        "packaging_copy": {
            "front": "丑得真实\n甜得直接",
            "back": "第一行\n第二行\n第三行",
            "side": "5kg · 12 枚\n80–85mm",
            "inside": "长得丑\n是它认真晒太阳的证据",
        },
        "structure": {
            "box_type": "牛皮纸天地盖礼盒",
            "dimensions": "360×260×90mm\n（演示）",
            "material": "350g 牛皮纸\n+ 瓦楞内托",
        },
    }

    data = render_label_png_bytes(
        output,
        batch,
        product,
        public_base_url="http://127.0.0.1:5173",
    )
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(data) > 50_000
