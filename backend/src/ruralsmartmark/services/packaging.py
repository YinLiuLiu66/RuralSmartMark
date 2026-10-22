from __future__ import annotations

import base64
import html
import re
from io import BytesIO
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont

from ..models import Batch, ProductProfile

DEFAULT_PALETTE = ["#B6402A", "#C9A46A", "#3F6B4F", "#F7F3EA"]
FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
)
_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _palette(product: ProductProfile) -> list[str]:
    roles = product.palette or {}
    values = [
        roles.get("apple", DEFAULT_PALETTE[0]),
        roles.get("kraft", DEFAULT_PALETTE[1]),
        roles.get("leaf", DEFAULT_PALETTE[2]),
        roles.get("paper", DEFAULT_PALETTE[3]),
    ]
    return [
        item if isinstance(item, str) and _HEX.match(item) else fallback
        for item, fallback in zip(values, DEFAULT_PALETTE, strict=True)
    ]


def _copy(output: dict) -> dict[str, str]:
    raw = output.get("packaging_copy") or {}
    return {
        "front": str(raw.get("front", "丑得真实，甜得直接")),
        "back": str(raw.get("back", "来自昭通昭阳区的高海拔果园。")),
        "side": str(raw.get("side", "5kg · 12 枚 · 80–85mm")),
        "inside": str(raw.get("inside", "长得丑，是它认真晒太阳的证据。")),
    }


def _structure(output: dict) -> dict[str, str]:
    raw = output.get("structure") or {}
    return {
        "box_type": str(raw.get("box_type", "牛皮纸天地盖礼盒")),
        "dimensions": str(raw.get("dimensions", "360×260×90mm")),
        "material": str(raw.get("material", "350g 牛皮纸 + 瓦楞内托")),
    }


def _trace_url(batch: Batch, public_base_url: str) -> str:
    return f"{public_base_url.rstrip('/')}/trace/{batch.trace_code or batch.code}"


def _qr_png(url: str, box_size: int = 12) -> bytes:
    qr = qrcode.QRCode(box_size=box_size, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    image = qr.make_image(fill_color="#1F2A24", back_color="white").convert("RGB")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _qr_data_uri(url: str) -> str:
    return "data:image/png;base64," + base64.b64encode(_qr_png(url, box_size=8)).decode()


def _wrap(text: str, width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        if char == "\n":
            lines.append(current)
            current = ""
            continue
        current += char
        if len(current) >= width:
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    return lines or [""]


def build_label_svg(
    output: dict,
    batch: Batch,
    product: ProductProfile,
    *,
    public_base_url: str,
) -> str:
    colors = _palette(product)
    primary, kraft, leaf, paper = colors[:4]
    copy = _copy(output)
    structure = _structure(output)
    concept = str(output.get("concept", "牛皮纸礼盒"))
    trace_url = _trace_url(batch, public_base_url)
    qr_uri = _qr_data_uri(trace_url)
    safe = html.escape

    back_lines = _wrap(copy["back"], 23)
    inside_lines = _wrap(copy["inside"], 24)
    back_svg = "".join(
        f'<text x="590" y="{365 + index * 38}" font-size="26" fill="#4A4F49">{safe(line)}</text>'
        for index, line in enumerate(back_lines[:4])
    )
    inside_svg = "".join(
        f'<text x="590" y="{710 + index * 36}" font-size="25" fill="#4A4F49">{safe(line)}</text>'
        for index, line in enumerate(inside_lines[:3])
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1000" viewBox="0 0 1600 1000">
  <rect width="1600" height="1000" fill="{paper}"/>
  <rect width="500" height="1000" fill="{primary}"/>
  <circle cx="410" cy="120" r="150" fill="{kraft}" opacity="0.28"/>
  <circle cx="80" cy="930" r="190" fill="{leaf}" opacity="0.22"/>
  <text x="58" y="96" font-family="Songti SC, Noto Serif SC, serif" font-size="38" fill="{paper}">乡土印记</text>
  <text x="58" y="138" font-family="PingFang SC, Noto Sans SC, sans-serif" font-size="20" fill="{paper}" opacity="0.86">乌蒙丑果 · 演示品牌</text>
  <text x="52" y="520" font-family="Songti SC, Noto Serif SC, serif" font-size="310" fill="{paper}">丑</text>
  <text x="58" y="600" font-family="PingFang SC, Noto Sans SC, sans-serif" font-size="24" fill="{paper}" opacity="0.9">长得丑，甜得认真</text>
  <text x="58" y="900" font-family="PingFang SC, Noto Sans SC, sans-serif" font-size="19" fill="{paper}" opacity="0.82">{safe(product.county)}</text>
  <text x="58" y="934" font-family="PingFang SC, Noto Sans SC, sans-serif" font-size="17" fill="{paper}" opacity="0.72">演示包装 · 非印刷稿</text>

  <text x="590" y="120" font-family="PingFang SC, Noto Sans SC, sans-serif" font-size="20" fill="{leaf}" letter-spacing="4">STORY / PACKAGING / TRACE</text>
  <text x="590" y="235" font-family="Songti SC, Noto Serif SC, serif" font-size="62" fill="#1F2A24">{safe(copy["front"])}</text>
  <text x="590" y="290" font-family="PingFang SC, Noto Sans SC, sans-serif" font-size="25" fill="#6B6F66">{safe(concept)}</text>
  <line x1="590" y1="320" x2="1480" y2="320" stroke="{kraft}" stroke-width="3"/>
  {back_svg}
  <text x="590" y="560" font-family="PingFang SC, Noto Sans SC, sans-serif" font-size="23" fill="{primary}">{safe(copy["side"])}</text>
  <text x="590" y="606" font-family="PingFang SC, Noto Sans SC, sans-serif" font-size="20" fill="#6B6F66">{safe(structure["box_type"])} · {safe(structure["dimensions"])}</text>
  <text x="590" y="642" font-family="PingFang SC, Noto Sans SC, sans-serif" font-size="18" fill="#6B6F66">{safe(structure["material"])}</text>
  <text x="590" y="680" font-family="Songti SC, Noto Serif SC, serif" font-size="26" fill="{leaf}">盒内一句话</text>
  {inside_svg}
  <rect x="1240" y="690" width="250" height="250" rx="16" fill="#FFFFFF" stroke="{kraft}" stroke-width="3"/>
  <image x="1258" y="708" width="214" height="214" href="{qr_uri}"/>
  <text x="1365" y="972" text-anchor="middle" font-family="PingFang SC, Noto Sans SC, sans-serif" font-size="18" fill="#6B6F66">扫码看这箱苹果的旅程</text>
</svg>"""


def _font(size: int, *, serif: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    ordered = FONT_CANDIDATES if serif else tuple(reversed(FONT_CANDIDATES))
    for path in ordered:
        if not Path(path).exists():
            continue
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    xy: tuple[int, int],
    max_width: int,
    fill: str,
    line_height: int,
    *,
    max_lines: int = 4,
) -> None:
    x, y = xy
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if draw.textlength(candidate, font=font) > max_width and current:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    for index, line in enumerate(lines[:max_lines]):
        draw.text((x, y + index * line_height), line, font=font, fill=fill)


def render_label_png(
    output: dict,
    batch: Batch,
    product: ProductProfile,
    path: Path,
    *,
    public_base_url: str,
) -> Path:
    colors = _palette(product)
    primary, kraft, leaf, paper = colors[:4]
    copy = _copy(output)
    structure = _structure(output)
    concept = str(output.get("concept", "牛皮纸礼盒"))
    trace_url = _trace_url(batch, public_base_url)

    image = Image.new("RGB", (1600, 1000), paper)
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, 500, 1000], fill=primary)
    draw.ellipse([260, -30, 560, 270], fill=kraft)
    draw.ellipse([-110, 740, 270, 1120], fill=leaf)

    serif_big = _font(310, serif=True)
    serif_title = _font(38, serif=True)
    serif_mid = _font(58, serif=True)
    sans_20 = _font(20)
    sans_24 = _font(24)
    sans_26 = _font(26)

    draw.text((58, 54), "乡土印记", font=serif_title, fill=paper)
    draw.text((58, 112), "乌蒙丑果 · 演示品牌", font=sans_20, fill=paper)
    draw.text((52, 210), "丑", font=serif_big, fill=paper)
    draw.text((58, 570), "长得丑，甜得认真", font=sans_24, fill=paper)
    draw.text((58, 880), product.county, font=sans_20, fill=paper)
    draw.text((58, 916), "演示包装 · 非印刷稿", font=sans_20, fill=paper)

    draw.text((590, 100), "STORY / PACKAGING / TRACE", font=sans_20, fill=leaf)
    draw.text((590, 170), copy["front"], font=serif_mid, fill="#1F2A24")
    draw.text((590, 248), concept, font=sans_24, fill="#6B6F66")
    draw.line([590, 300, 1480, 300], fill=kraft, width=3)
    _draw_wrapped(draw, copy["back"], sans_26, (590, 330), 870, "#4A4F49", 40, max_lines=4)

    draw.text((590, 530), copy["side"], font=sans_24, fill=primary)
    draw.text(
        (590, 574),
        f"{structure['box_type']} · {structure['dimensions']}",
        font=sans_20,
        fill="#6B6F66",
    )
    draw.text((590, 608), structure["material"], font=sans_20, fill="#6B6F66")
    draw.text((590, 660), "盒内一句话", font=_font(26, serif=True), fill=leaf)
    _draw_wrapped(draw, copy["inside"], sans_26, (590, 702), 600, "#4A4F49", 38, max_lines=3)

    qr = Image.open(BytesIO(_qr_png(trace_url, box_size=10))).convert("RGB").resize((214, 214))
    draw.rounded_rectangle([1240, 690, 1490, 940], radius=16, fill="white", outline=kraft, width=3)
    image.paste(qr, (1258, 708))
    draw.text((1365, 950), "扫码看这箱苹果的旅程", font=sans_20, fill="#6B6F66", anchor="ma")

    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True)
    return path
