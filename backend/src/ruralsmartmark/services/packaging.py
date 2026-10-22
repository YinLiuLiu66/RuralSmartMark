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
_FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
BUNDLED_FONTS = {
    ("serif", False): _FONT_DIR / "NotoSerifSC-Regular.otf",
    ("serif", True): _FONT_DIR / "NotoSerifSC-Bold.otf",
    ("sans", False): _FONT_DIR / "NotoSansSC-Regular.otf",
    ("sans", True): _FONT_DIR / "NotoSansSC-Bold.otf",
}
SERIF_FALLBACKS = (
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
)
SANS_FALLBACKS = (
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
)
_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
_FONT_NAME = "Noto Serif SC, Songti SC, serif"
_SANS_NAME = "Noto Sans SC, PingFang SC, sans-serif"


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


def render_qr_png(url: str, box_size: int = 12) -> bytes:
    qr = qrcode.QRCode(box_size=box_size, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    image = qr.make_image(fill_color="#1F2A24", back_color="white").convert("RGB")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _qr_data_uri(url: str) -> str:
    return "data:image/png;base64," + base64.b64encode(render_qr_png(url, box_size=8)).decode()


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
  <text x="58" y="96" font-family="{_FONT_NAME}" font-size="38" fill="{paper}">乡土印记</text>
  <text x="58" y="138" font-family="{_SANS_NAME}" font-size="20" fill="{paper}" opacity="0.86">乌蒙丑果 · 演示品牌</text>
  <text x="52" y="520" font-family="{_FONT_NAME}" font-size="310" fill="{paper}">丑</text>
  <text x="58" y="600" font-family="{_SANS_NAME}" font-size="24" fill="{paper}" opacity="0.9">长得丑，甜得认真</text>
  <text x="58" y="900" font-family="{_SANS_NAME}" font-size="19" fill="{paper}" opacity="0.82">{safe(product.county)}</text>
  <text x="58" y="934" font-family="{_SANS_NAME}" font-size="17" fill="{paper}" opacity="0.72">演示包装 · 非印刷稿</text>

  <text x="590" y="120" font-family="{_SANS_NAME}" font-size="20" fill="{leaf}" letter-spacing="4">STORY / PACKAGING / TRACE</text>
  <text x="590" y="235" font-family="{_FONT_NAME}" font-size="62" fill="#1F2A24">{safe(copy["front"])}</text>
  <text x="590" y="290" font-family="{_SANS_NAME}" font-size="25" fill="#6B6F66">{safe(concept)}</text>
  <line x1="590" y1="320" x2="1480" y2="320" stroke="{kraft}" stroke-width="3"/>
  {back_svg}
  <text x="590" y="560" font-family="{_SANS_NAME}" font-size="23" fill="{primary}">{safe(copy["side"])}</text>
  <text x="590" y="606" font-family="{_SANS_NAME}" font-size="20" fill="#6B6F66">{safe(structure["box_type"])} · {safe(structure["dimensions"])}</text>
  <text x="590" y="642" font-family="{_SANS_NAME}" font-size="18" fill="#6B6F66">{safe(structure["material"])}</text>
  <text x="590" y="680" font-family="{_FONT_NAME}" font-size="26" fill="{leaf}">盒内一句话</text>
  {inside_svg}
  <rect x="1240" y="690" width="250" height="250" rx="16" fill="#FFFFFF" stroke="{kraft}" stroke-width="3"/>
  <image x="1258" y="708" width="214" height="214" href="{qr_uri}"/>
  <text x="1365" y="972" text-anchor="middle" font-family="{_SANS_NAME}" font-size="18" fill="#6B6F66">扫码看这箱苹果的旅程</text>
</svg>"""


def _font(
    size: int, *, serif: bool = False, bold: bool = False
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    family = "serif" if serif else "sans"
    ordered = [BUNDLED_FONTS[(family, bold)]]
    ordered.extend(SERIF_FALLBACKS if serif else SANS_FALLBACKS)
    for path in ordered:
        if not Path(path).exists():
            continue
        try:
            return ImageFont.truetype(str(path), size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
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
    return lines or [""]


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
    lines = _wrap_lines(draw, text, font, max_width)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:-1] + "…"
    x, y = xy
    for index, line in enumerate(lines):
        draw.text((x, y + index * line_height), line, font=font, fill=fill)


def _fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    size: int,
    *,
    serif: bool = False,
    bold: bool = False,
    min_size: int = 14,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    while size > min_size:
        font = _font(size, serif=serif, bold=bold)
        if draw.textlength(text, font=font) <= max_width:
            return font
        size -= 2
    return _font(min_size, serif=serif, bold=bold)


def _draw_wrapped_fit(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    max_width: int,
    fill: str,
    line_height: int,
    *,
    size: int,
    max_lines: int,
    serif: bool = False,
    bold: bool = False,
    min_size: int = 16,
) -> None:
    while size > min_size:
        font = _font(size, serif=serif, bold=bold)
        if len(_wrap_lines(draw, text, font, max_width)) <= max_lines:
            break
        size -= 2
    _draw_wrapped(
        draw,
        text,
        _font(size, serif=serif, bold=bold),
        xy,
        max_width,
        fill,
        line_height,
        max_lines=max_lines,
    )


def _render_label_image(
    output: dict,
    batch: Batch,
    product: ProductProfile,
    *,
    public_base_url: str,
) -> Image.Image:
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

    serif_big = _font(310, serif=True, bold=True)
    serif_title = _font(38, serif=True, bold=True)
    sans_20 = _font(20)
    sans_24 = _font(24)

    draw.text((58, 54), "乡土印记", font=serif_title, fill=paper)
    draw.text((58, 112), "乌蒙丑果 · 演示品牌", font=sans_20, fill=paper)
    draw.text((52, 210), "丑", font=serif_big, fill=paper)
    draw.text((58, 570), "长得丑，甜得认真", font=sans_24, fill=paper)
    county_font = _fit_font(draw, product.county, 400, 20, min_size=14)
    draw.text((58, 880), product.county, font=county_font, fill=paper)
    draw.text((58, 916), "演示包装 · 非印刷稿", font=sans_20, fill=paper)

    draw.text((590, 100), "STORY / PACKAGING / TRACE", font=sans_20, fill=leaf)
    headline_font = _fit_font(draw, copy["front"], 890, 58, serif=True, bold=True, min_size=26)
    draw.text((590, 170), copy["front"], font=headline_font, fill="#1F2A24")
    _draw_wrapped_fit(
        draw,
        concept,
        (590, 248),
        870,
        "#6B6F66",
        30,
        size=24,
        max_lines=2,
        min_size=16,
    )
    draw.line([590, 300, 1480, 300], fill=kraft, width=3)
    _draw_wrapped_fit(
        draw,
        copy["back"],
        (590, 330),
        870,
        "#4A4F49",
        40,
        size=26,
        max_lines=5,
        min_size=18,
    )

    side_font = _fit_font(draw, copy["side"], 870, 24, min_size=16)
    draw.text((590, 530), copy["side"], font=side_font, fill=primary)
    structure_line = f"{structure['box_type']} · {structure['dimensions']}"
    structure_font = _fit_font(draw, structure_line, 870, 20, min_size=14)
    draw.text((590, 574), structure_line, font=structure_font, fill="#6B6F66")
    material_font = _fit_font(draw, structure["material"], 870, 20, min_size=14)
    draw.text((590, 608), structure["material"], font=material_font, fill="#6B6F66")
    draw.text((590, 660), "盒内一句话", font=_font(26, serif=True, bold=True), fill=leaf)
    _draw_wrapped_fit(
        draw,
        copy["inside"],
        (590, 702),
        600,
        "#4A4F49",
        38,
        size=26,
        max_lines=3,
        min_size=18,
    )

    qr = (
        Image.open(BytesIO(render_qr_png(trace_url, box_size=10))).convert("RGB").resize((214, 214))
    )
    draw.rounded_rectangle([1240, 690, 1490, 940], radius=16, fill="white", outline=kraft, width=3)
    image.paste(qr, (1258, 708))
    draw.text((1365, 950), "扫码看这箱苹果的旅程", font=sans_20, fill="#6B6F66", anchor="ma")
    return image


def render_label_png_bytes(
    output: dict,
    batch: Batch,
    product: ProductProfile,
    *,
    public_base_url: str,
) -> bytes:
    image = _render_label_image(output, batch, product, public_base_url=public_base_url)
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def render_label_png(
    output: dict,
    batch: Batch,
    product: ProductProfile,
    path: Path,
    *,
    public_base_url: str,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        render_label_png_bytes(output, batch, product, public_base_url=public_base_url)
    )
    return path
