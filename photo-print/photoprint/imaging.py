"""Open any photo, lay it out on the paper, and render print-ready page rasters."""
from __future__ import annotations

import io
import math
import os
from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ImageCms, ImageFilter, ImageOps

from . import color

try:
    import pillow_heif
except ImportError:  # HEIC support is optional but strongly recommended
    pillow_heif = None
try:
    import rawpy
except ImportError:
    rawpy = None

Image.MAX_IMAGE_PIXELS = 400_000_000

HEIF_EXT = {".heic", ".heif", ".hif"}
RAW_EXT = {".dng", ".cr2", ".cr3", ".crw", ".nef", ".nrw", ".arw", ".srf", ".sr2", ".raf",
           ".orf", ".rw2", ".pef", ".srw", ".3fr", ".erf", ".kdc", ".mrw", ".x3f", ".iiq",
           ".mos", ".rwl", ".gpr"}
SUPPORTED_HINT = "HEIC/HEIF, JPEG, PNG, TIFF, WebP, AVIF, BMP, GIF, RAW (DNG/CR2/CR3/NEF/ARW/RAF/ORF/RW2...)"


@dataclass
class Photo:
    pixels: np.ndarray            # HxWx3, uint8 or uint16, encoded in `colorspace`
    colorspace: color.ColorSpace
    fmt: str
    name: str = ""
    bit_depth: int = 8

    @property
    def size(self):
        return self.pixels.shape[1], self.pixels.shape[0]

    def describe(self) -> dict:
        w, h = self.size
        return {"name": self.name, "format": self.fmt, "width": w, "height": h,
                "bit_depth": self.bit_depth, "colorspace": self.colorspace.name}


# ---------------------------------------------------------------- decoding

def load(path_or_bytes, name: str | None = None) -> Photo:
    if isinstance(path_or_bytes, (bytes, bytearray)):
        data, name = bytes(path_or_bytes), name or "photo"
    else:
        name = name or os.path.basename(path_or_bytes)
        with open(path_or_bytes, "rb") as f:
            data = f.read()
    ext = os.path.splitext(name)[1].lower()
    is_heif = ext in HEIF_EXT or data[4:12] in (b"ftypheic", b"ftypheix", b"ftypmif1",
                                                b"ftypmsf1", b"ftyphevc", b"ftypheim")
    if is_heif:
        return _load_heif(data, name)
    if ext in RAW_EXT:
        return _load_raw(data, name)
    try:
        return _load_pillow(data, name)
    except Exception as exc:  # unknown extension: maybe a RAW file after all
        if rawpy is not None:
            try:
                return _load_raw(data, name)
            except Exception:
                pass
        raise ValueError(f"Cannot open {name}: {exc}. Supported: {SUPPORTED_HINT}") from exc


def _load_heif(data: bytes, name: str) -> Photo:
    if pillow_heif is None:
        raise RuntimeError("HEIC needs pillow-heif: pip install pillow-heif")
    heif = pillow_heif.open_heif(io.BytesIO(data), convert_hdr_to_8bit=False)
    arr = np.asarray(heif)
    if arr.ndim == 2:
        arr = np.repeat(arr[..., None], 3, axis=-1)
    arr = arr[..., :3]
    icc = heif.info.get("icc_profile")
    cs = color.from_icc(icc) if icc else None
    if cs is None and heif.info.get("nclx_profile"):
        cs = color.from_nclx(heif.info["nclx_profile"])
    # libheif already applied the rotation/mirror boxes; EXIF orientation is not reused.
    return Photo(np.ascontiguousarray(arr), cs or color.SRGB, "HEIF", name,
                 heif.info.get("bit_depth", 8))


def _load_raw(data: bytes, name: str) -> Photo:
    if rawpy is None:
        raise RuntimeError("RAW files need rawpy: pip install rawpy")
    with rawpy.imread(io.BytesIO(data)) as raw:
        # Linear 16-bit Adobe RGB keeps the camera's colours (much wider than sRGB);
        # our gamut mapping then handles the squeeze into what prints.
        arr = raw.postprocess(output_color=rawpy.ColorSpace.Adobe, gamma=(1, 1),
                              output_bps=16, use_camera_wb=True, no_auto_bright=False,
                              user_sat=None)
    return Photo(arr, color.ADOBE_RGB_LINEAR, "RAW", name, 16)


def _load_pillow(data: bytes, name: str) -> Photo:
    im = Image.open(io.BytesIO(data))
    fmt = im.format or "image"
    im = ImageOps.exif_transpose(im)
    icc = im.info.get("icc_profile")
    cs = color.from_icc(icc) if icc else None

    if im.mode == "CMYK" or (icc and cs is None and im.mode in ("RGB", "RGBA")):
        # LUT-based or CMYK profile: let LittleCMS do it (perceptual + black point comp.)
        src = ImageCms.ImageCmsProfile(io.BytesIO(icc)) if icc else None
        base = im.convert("RGB") if im.mode == "RGBA" else im
        if src is not None:
            im = ImageCms.profileToProfile(
                base, src, ImageCms.createProfile("sRGB"),
                renderingIntent=ImageCms.Intent.PERCEPTUAL, outputMode="RGB",
                flags=ImageCms.Flags.BLACKPOINTCOMPENSATION)
        else:
            im = base.convert("RGB")
        cs = color.SRGB

    if cs is None:
        cs = _exif_colorspace(im) or color.SRGB

    if im.mode in ("I;16", "I;16B", "I;16L", "I"):
        arr = np.asarray(im).astype(np.float32)
        arr = (arr / (65535 if arr.max() > 255 else 255) * 65535).astype(np.uint16)
        return Photo(np.repeat(arr[..., None], 3, axis=-1), cs, fmt, name, 16)
    if im.mode == "F":
        arr = (np.clip(np.asarray(im), 0, 1) * 65535).astype(np.uint16)
        return Photo(np.repeat(arr[..., None], 3, axis=-1), cs, fmt, name, 16)
    if im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info):
        rgba = im.convert("RGBA")
        white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        im = Image.alpha_composite(white, rgba)
    return Photo(np.asarray(im.convert("RGB")), cs, fmt, name, 8)


def _exif_colorspace(im: Image.Image):
    """Cameras that shoot Adobe RGB flag it in EXIF instead of embedding a profile."""
    try:
        exif = im.getexif()
        if exif.get_ifd(0x8769).get(0xA001) == 0xFFFF:
            interop = exif.get_ifd(0xA005).get(0x0001)
            if interop and str(interop).strip("\0 ") == "R03":
                return color.ADOBE_RGB
    except Exception:
        pass
    return None


# ---------------------------------------------------------------- paper & layout

@dataclass(frozen=True)
class Paper:
    key: str
    label: str
    w_mm: float
    h_mm: float
    ipp: str

    @property
    def ipp_dims(self):
        return int(round(self.w_mm * 100)), int(round(self.h_mm * 100))


PAPERS = {p.key: p for p in [
    Paper("4x6", "4x6 in / 10x15 cm (photo)", 101.6, 152.4, "na_index-4x6_4x6in"),
    Paper("10x15", "10x15 cm", 100, 150, "om_small-photo_100x150mm"),
    Paper("5x7", "5x7 in / 13x18 cm", 127, 177.8, "na_5x7_5x7in"),
    Paper("3.5x5", "3.5x5 in (L)", 88.9, 127, "oe_photo-l_3.5x5in"),
    Paper("8x10", "8x10 in", 203.2, 254, "na_govt-letter_8x10in"),
    Paper("A6", "A6", 105, 148, "iso_a6_105x148mm"),
    Paper("A5", "A5", 148, 210, "iso_a5_148x210mm"),
    Paper("A4", "A4", 210, 297, "iso_a4_210x297mm"),
    Paper("letter", "Letter", 215.9, 279.4, "na_letter_8.5x11in"),
    Paper("legal", "Legal", 215.9, 355.6, "na_legal_8.5x14in"),
    Paper("hagaki", "Hagaki 100x148", 100, 148, "jpn_hagaki_100x148mm"),
]}


def paper_from(value: str) -> Paper:
    if value in PAPERS:
        return PAPERS[value]
    for p in PAPERS.values():
        if value.lower() in (p.key.lower(), p.ipp.lower()):
            return p
    try:  # custom "WxHmm"
        w, h = value.lower().removesuffix("mm").split("x")
        w, h = float(w), float(h)
        return Paper(value, f"{w:g}x{h:g} mm", w, h, f"custom_{w:g}x{h:g}mm_{w:g}x{h:g}mm")
    except ValueError:
        raise ValueError(f"Unknown paper '{value}'. Use one of {', '.join(PAPERS)} or WxHmm")


@dataclass
class PrintSettings:
    paper: str = "4x6"
    media_type: str = "glossy"        # glossy | matte | plain | brochure | auto | <ipp keyword>
    quality: str = "best"             # draft | normal | best
    borderless: bool = True
    fit: str = "fill"                 # fill (crop to paper) | fit (whole photo, white bars)
    layout: str = "1"                 # photos per page: 1, 2, 4, 6, 9 or "CxR"
    copies: int = 1
    color_mode: str = "color"         # color | monochrome (grey photo, colour inks) | mono-black
    dpi: int = 0                      # 0 = auto (300 or 600 depending on source detail)
    brightness: float = 1.0           # print compensation 0..2
    saturation: float = 1.0
    sharpen: float = 1.0              # 0..2
    gamut: str = "compress"           # compress | clip
    auto_rotate: bool = True
    margin_mm: float = 3.0            # used when not borderless (printer value wins)
    gap_mm: float = 3.0
    media_source: str = "auto"
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "PrintSettings":
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        s = cls(**known)
        s.copies, s.dpi = int(s.copies), int(s.dpi or 0)
        for k in ("brightness", "saturation", "sharpen", "margin_mm", "gap_mm"):
            setattr(s, k, float(getattr(s, k)))
        for k in ("borderless", "auto_rotate"):
            v = getattr(s, k)
            setattr(s, k, v if isinstance(v, bool) else str(v).lower() in ("1", "true", "yes", "on"))
        return s


def grid_for(layout: str) -> tuple[int, int]:
    layout = str(layout).lower()
    if "x" in layout:
        c, r = layout.split("x")
        return max(1, int(c)), max(1, int(r))
    return {"1": (1, 1), "2": (1, 2), "3": (1, 3), "4": (2, 2), "6": (2, 3), "8": (2, 4),
            "9": (3, 3), "12": (3, 4), "16": (4, 4), "20": (4, 5)}.get(layout, (1, 1))


def _cells(page_w, page_h, margins, cols, rows, gap):
    top, right, bottom, left = margins
    area_w, area_h = page_w - left - right, page_h - top - bottom
    cw, ch = (area_w - gap * (cols - 1)) / cols, (area_h - gap * (rows - 1)) / rows
    return [(left + c * (cw + gap), top + r * (ch + gap), cw, ch)
            for r in range(rows) for c in range(cols)]


def _resize_channels(arr: np.ndarray, w: int, h: int) -> np.ndarray:
    """High quality Lanczos resize on float data (keeps 10/16-bit precision)."""
    scale = 65535.0 if arr.dtype == np.uint16 else 255.0
    if arr.dtype == np.uint8:
        return np.asarray(Image.fromarray(arr).resize((w, h), Image.LANCZOS, reducing_gap=3.0),
                          dtype=np.float32) / 255.0
    out = np.empty((h, w, 3), np.float32)
    for i in range(3):
        ch = Image.fromarray(arr[..., i].astype(np.float32) / scale, "F")
        out[..., i] = np.asarray(ch.resize((w, h), Image.LANCZOS, reducing_gap=3.0))
    return np.clip(out, 0, 1)


def place_photo(photo: Photo, box_w: int, box_h: int, s: PrintSettings) -> Image.Image:
    """Crop/rotate/resize one photo to a box (pixels) and colour-convert it."""
    arr = photo.pixels
    h, w = arr.shape[:2]
    if s.auto_rotate and (w > h) != (box_w > box_h) and w != h and box_w != box_h:
        arr = np.rot90(arr, 1 if (w > h) else -1)
        h, w = arr.shape[:2]
    target_ratio = box_w / box_h
    if s.fit == "fill":
        if w / h > target_ratio:
            nw = max(1, round(h * target_ratio))
            x0 = (w - nw) // 2
            arr = arr[:, x0:x0 + nw]
        else:
            nh = max(1, round(w / target_ratio))
            y0 = (h - nh) // 2
            arr = arr[y0:y0 + nh]
        out_w, out_h = box_w, box_h
    else:
        f = min(box_w / w, box_h / h)
        out_w, out_h = max(1, round(w * f)), max(1, round(h * f))
    src_w = arr.shape[1]
    small = _resize_channels(np.ascontiguousarray(arr), out_w, out_h)
    enc = color.to_print_srgb(small, photo.colorspace, gamut=s.gamut, brightness=s.brightness,
                              saturation=s.saturation, monochrome=s.color_mode != "color")
    img = Image.fromarray(color.to_uint8(enc))
    if s.sharpen > 0:
        upscale = out_w / src_w
        radius = max(0.6, (s.dpi or 300) / 300 * 0.9)
        amount = int(55 * s.sharpen * (0.5 if upscale > 1.5 else 1.0))
        img = img.filter(ImageFilter.UnsharpMask(radius=radius, percent=amount, threshold=2))
    return img


def choose_dpi(photos: list[Photo], s: PrintSettings, cell_w_mm: float, cell_h_mm: float) -> int:
    if s.dpi:
        return s.dpi
    ppi = []
    for p in photos:
        w, h = sorted(p.size)
        cw, ch = sorted((cell_w_mm, cell_h_mm))
        ppi.append(min(w / (cw / 25.4), h / (ch / 25.4)))
    # 600 ppi only pays off when the photo really carries that much detail.
    return 600 if ppi and min(ppi) >= 450 and s.quality == "best" else 300


def effective_ppi(photo: Photo, paper: Paper, s: PrintSettings) -> float:
    cols, rows = grid_for(s.layout)
    cw, ch = paper.w_mm / cols, paper.h_mm / rows
    w, h = sorted(photo.size)
    a, b = sorted((cw, ch))
    return min(w / (a / 25.4), h / (b / 25.4))


def render_pages(photos: list[Photo], s: PrintSettings,
                 margins_mm: tuple | None = None) -> tuple[list[Image.Image], int, Paper]:
    """Returns (page rasters, dpi, paper). Pages are always portrait, sized exactly
    to the paper, so the printer can place them 1:1 (no surprise scaling)."""
    paper = paper_from(s.paper)
    if margins_mm is None:
        margins_mm = (0, 0, 0, 0) if s.borderless else (s.margin_mm,) * 4
    cols, rows = grid_for(s.layout)
    cells_mm = _cells(paper.w_mm, paper.h_mm, margins_mm, cols, rows,
                      s.gap_mm if cols * rows > 1 else 0)
    dpi = choose_dpi(photos, s, cells_mm[0][2], cells_mm[0][3])
    px = lambda mm: int(round(mm / 25.4 * dpi))
    per_page = cols * rows
    pages = []
    for start in range(0, len(photos), per_page):
        page = Image.new("RGB", (px(paper.w_mm), px(paper.h_mm)), "white")
        for photo, (x, y, w, h) in zip(photos[start:start + per_page], cells_mm):
            bw, bh = px(x + w) - px(x), px(y + h) - px(y)
            img = place_photo(photo, bw, bh, s)
            page.paste(img, (px(x) + (bw - img.width) // 2, px(y) + (bh - img.height) // 2))
        pages.append(page)
    return pages, dpi, paper


# ---------------------------------------------------------------- encoding

def srgb_icc() -> bytes:
    return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


def encode_jpeg(img: Image.Image, dpi: int, quality: int = 95) -> bytes:
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality, subsampling=0, dpi=(dpi, dpi),
             icc_profile=srgb_icc(), optimize=True)
    return buf.getvalue()


def encode_pdf(pages: list[Image.Image], dpi: int, paper: Paper) -> bytes:
    """Minimal PDF: one full-bleed JPEG (4:4:4, q95) per page, MediaBox = paper size."""
    w_pt, h_pt = paper.w_mm / 25.4 * 72, paper.h_mm / 25.4 * 72
    objs: list[bytes] = []
    kids = []
    for i, page in enumerate(pages):
        jpg = encode_jpeg(page, dpi)
        img_id, content_id, page_id = 3 + 3 * i, 4 + 3 * i, 5 + 3 * i
        kids.append(page_id)
        objs.append(b"<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace /DeviceRGB"
                    b" /BitsPerComponent 8 /Filter /DCTDecode /Length %d >>\nstream\n"
                    % (page.width, page.height, len(jpg)) + jpg + b"\nendstream")
        content = b"q %.4f 0 0 %.4f 0 0 cm /Im0 Do Q" % (w_pt, h_pt)
        objs.append(b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream")
        objs.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.4f %.4f] /Contents %d 0 R"
                    b" /Resources << /XObject << /Im0 %d 0 R >> >> >>"
                    % (w_pt, h_pt, content_id, img_id))
    head = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [%s] /Count %d >>"
            % (b" ".join(b"%d 0 R" % k for k in kids), len(kids))]
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for n, body in enumerate(head + objs, start=1):
        offsets.append(out.tell())
        out.write(b"%d 0 obj\n" % n + body + b"\nendobj\n")
    xref = out.tell()
    out.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(offsets) + 1))
    for off in offsets:
        out.write(b"%010d 00000 n \n" % off)
    out.write(b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
              % (len(offsets) + 1, xref))
    return out.getvalue()


def preview_jpeg(page: Image.Image, max_side: int = 900) -> bytes:
    p = page.copy()
    p.thumbnail((max_side, max_side), Image.LANCZOS)
    buf = io.BytesIO()
    p.save(buf, "JPEG", quality=85, icc_profile=srgb_icc())
    return buf.getvalue()
