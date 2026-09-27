"""Colour science: work out which colour space a photo was saved in, then turn it
into print-ready sRGB without losing the look the camera recorded.

Why sRGB: the HP Smart Tank 580 (like every AirPrint / IPP Everywhere / Mopria
printer, and the HP Windows driver) treats incoming RGB as sRGB and does its own
sRGB -> ink separation. Phones save in Display P3 (iPhone, most flagships) or
wider, so sending those numbers untouched makes the printer read them as sRGB:
the image prints dull and shifted. We convert properly, and squeeze the colours
that sRGB cannot hold with a smooth chroma compression instead of hard clipping
(hard clipping flattens skies, flowers and skin into flat patches).

All maths runs in float32 on already-resized pixels, so 10/12/16-bit sources
(HEIC, RAW, 16-bit TIFF/PNG) keep their precision until the final dithered 8-bit.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field

import numpy as np

# ICC profile connection space white (D50) and the usual D65 display white.
D50_XYZ = np.array([0.9642, 1.0, 0.8249])
D65_xy = (0.3127, 0.3290)
D50_xy = (0.3457, 0.3585)

_BRADFORD = np.array([[0.8951, 0.2664, -0.1614],
                      [-0.7502, 1.7135, 0.0367],
                      [0.0389, -0.0685, 1.0296]])


def _xy_to_xyz(x: float, y: float) -> np.ndarray:
    return np.array([x / y, 1.0, (1 - x - y) / y])


def _adapt(src_white: np.ndarray, dst_white: np.ndarray) -> np.ndarray:
    s, d = _BRADFORD @ src_white, _BRADFORD @ dst_white
    return np.linalg.inv(_BRADFORD) @ np.diag(d / s) @ _BRADFORD


def primaries_matrix(primaries, white_xy) -> np.ndarray:
    """Linear RGB -> XYZ(D50) matrix, Bradford-adapted like an ICC profile."""
    p = np.column_stack([_xy_to_xyz(*xy) for xy in primaries])
    w = _xy_to_xyz(*white_xy)
    m = p * np.linalg.solve(p, w)
    return _adapt(w, D50_XYZ) @ m


# ---------------------------------------------------------------- transfer curves

@dataclass
class Curve:
    """Decodes encoded values (0..1) to linear light. kind: para|table|linear."""
    kind: str
    params: tuple = ()
    table: np.ndarray | None = None

    def decode(self, x: np.ndarray) -> np.ndarray:
        if self.kind == "linear":
            return x
        if self.kind == "table":
            t = self.table
            return np.interp(x, np.linspace(0, 1, len(t)), t).astype(np.float32)
        return _para(x, self.params)


def _para(x, p):
    """ICC parametricCurveType, function types 0-4."""
    ftype, a = p[0], p[1:]
    x = np.clip(x, 0, 1)
    if ftype == 0:
        return np.power(x, a[0])
    g, pa, pb = a[0], a[1], a[2]
    if ftype == 1:
        return np.where(x >= -pb / pa, np.power(np.maximum(pa * x + pb, 0), g), 0)
    if ftype == 2:
        return np.where(x >= -pb / pa, np.power(np.maximum(pa * x + pb, 0), g), 0) + a[3]
    if ftype == 3:
        c, d = a[3], a[4]
        return np.where(x >= d, np.power(np.maximum(pa * x + pb, 0), g), c * x)
    c, d, e, f = a[3], a[4], a[5], a[6]
    return np.where(x >= d, np.power(np.maximum(pa * x + pb, 0), g) + e, c * x + f)


SRGB_CURVE = Curve("para", (3, 2.4, 1 / 1.055, 0.055 / 1.055, 1 / 12.92, 0.04045))
GAMMA22_CURVE = Curve("para", (0, 563 / 256))
GAMMA18_CURVE = Curve("para", (0, 1.8))
BT709_CURVE = Curve("para", (3, 1 / 0.45, 1 / 1.099, 0.099 / 1.099, 1 / 4.5, 0.081))
LINEAR_CURVE = Curve("linear")

SRGB_PRIMARIES = ((0.64, 0.33), (0.30, 0.60), (0.15, 0.06))
P3_PRIMARIES = ((0.680, 0.320), (0.265, 0.690), (0.150, 0.060))
BT2020_PRIMARIES = ((0.708, 0.292), (0.170, 0.797), (0.131, 0.046))
ADOBE_PRIMARIES = ((0.64, 0.33), (0.21, 0.71), (0.15, 0.06))
PROPHOTO_PRIMARIES = ((0.7347, 0.2653), (0.1596, 0.8404), (0.0366, 0.0001))


@dataclass
class ColorSpace:
    name: str
    matrix: np.ndarray                      # linear RGB -> XYZ D50
    curves: list = field(default_factory=lambda: [SRGB_CURVE] * 3)
    hdr: str | None = None                  # None | "pq" | "hlg"

    def is_srgb(self) -> bool:
        return (self.hdr is None and np.allclose(self.matrix, SRGB.matrix, atol=2e-3)
                and all(c is SRGB_CURVE or _close_to_srgb(c) for c in self.curves))


def _close_to_srgb(curve: Curve) -> bool:
    x = np.linspace(0, 1, 64, dtype=np.float32)
    return np.abs(curve.decode(x) - SRGB_CURVE.decode(x)).max() < 2e-3


SRGB = ColorSpace("sRGB", primaries_matrix(SRGB_PRIMARIES, D65_xy))
DISPLAY_P3 = ColorSpace("Display P3", primaries_matrix(P3_PRIMARIES, D65_xy))
ADOBE_RGB = ColorSpace("Adobe RGB (1998)", primaries_matrix(ADOBE_PRIMARIES, D65_xy),
                       [GAMMA22_CURVE] * 3)
ADOBE_RGB_LINEAR = ColorSpace("Adobe RGB (linear, from RAW)", ADOBE_RGB.matrix, [LINEAR_CURVE] * 3)
PROPHOTO = ColorSpace("ProPhoto RGB", primaries_matrix(PROPHOTO_PRIMARIES, D50_xy), [GAMMA18_CURVE] * 3)

_XYZ_TO_LINEAR_SRGB = np.linalg.inv(SRGB.matrix)
_LUMA = SRGB.matrix[1] / SRGB.matrix[1].sum()   # Y weights of linear sRGB


# ---------------------------------------------------------------- ICC / nclx parsing

def from_icc(data: bytes) -> ColorSpace | None:
    """Matrix/TRC RGB profiles (sRGB, Display P3, Adobe, ProPhoto, Rec.2020...).
    Returns None for LUT-only or non-RGB profiles; the caller then uses LittleCMS."""
    try:
        if len(data) < 132 or data[16:20] != b"RGB ":
            return None
        count = struct.unpack(">I", data[128:132])[0]
        tags = {}
        for i in range(count):
            sig, off, size = struct.unpack(">4sII", data[132 + 12 * i:144 + 12 * i])
            tags[sig] = data[off:off + size]
        cols = []
        for sig in (b"rXYZ", b"gXYZ", b"bXYZ"):
            t = tags[sig]
            cols.append([v / 65536 for v in struct.unpack(">3i", t[8:20])])
        curves = [_parse_curve(tags[s]) for s in (b"rTRC", b"gTRC", b"bTRC")]
        name = _icc_description(tags.get(b"desc", b"")) or "ICC RGB"
        return ColorSpace(name, np.array(cols).T, curves)
    except (KeyError, struct.error, ValueError):
        return None


def _parse_curve(t: bytes) -> Curve:
    if t[:4] == b"curv":
        n = struct.unpack(">I", t[8:12])[0]
        if n == 0:
            return LINEAR_CURVE
        if n == 1:
            return Curve("para", (0, struct.unpack(">H", t[12:14])[0] / 256))
        table = np.array(struct.unpack(f">{n}H", t[12:12 + 2 * n]), dtype=np.float32) / 65535
        if n == 2 and table[0] == 0 and table[1] == 1:
            return LINEAR_CURVE
        return Curve("table", table=table)
    if t[:4] == b"para":
        ftype = struct.unpack(">H", t[8:10])[0]
        nparams = {0: 1, 1: 3, 2: 4, 3: 5, 4: 7}[ftype]
        vals = [v / 65536 for v in struct.unpack(f">{nparams}i", t[12:12 + 4 * nparams])]
        return Curve("para", (ftype, *vals))
    raise ValueError("unsupported curve")


def _icc_description(t: bytes) -> str:
    if t[:4] == b"desc":
        n = struct.unpack(">I", t[8:12])[0]
        return t[12:12 + n].rstrip(b"\0").decode("latin-1", "ignore")
    if t[:4] == b"mluc":
        n, rec = struct.unpack(">II", t[8:16])
        if n:
            length, off = struct.unpack(">II", t[20:28])
            return t[off:off + length].decode("utf-16-be", "ignore")
    return ""


def from_nclx(nclx: dict) -> ColorSpace:
    """HEIF/AVIF colour boxes (common on Android phones and HDR shots)."""
    prim = nclx.get("color_primaries", 1)
    tc = nclx.get("transfer_characteristics", 13)
    try:
        primaries = ((nclx["color_primary_red_x"], nclx["color_primary_red_y"]),
                     (nclx["color_primary_green_x"], nclx["color_primary_green_y"]),
                     (nclx["color_primary_blue_x"], nclx["color_primary_blue_y"]))
        white = (nclx["color_primary_white_x"], nclx["color_primary_white_y"])
    except KeyError:
        primaries, white = {9: BT2020_PRIMARIES, 11: P3_PRIMARIES, 12: P3_PRIMARIES}.get(
            prim, SRGB_PRIMARIES), (0.314, 0.351) if prim == 11 else D65_xy
    names = {1: "sRGB/BT.709", 9: "BT.2020", 11: "DCI-P3", 12: "Display P3"}
    curve, hdr = SRGB_CURVE, None
    if tc == 8:
        curve = LINEAR_CURVE
    elif tc in (1, 6, 14, 15):
        curve = BT709_CURVE
    elif tc == 16:
        curve, hdr = LINEAR_CURVE, "pq"
    elif tc == 18:
        curve, hdr = LINEAR_CURVE, "hlg"
    name = names.get(prim, "custom primaries") + (f" {hdr.upper()} HDR" if hdr else "")
    return ColorSpace(name, primaries_matrix(primaries, white), [curve] * 3, hdr)


# ---------------------------------------------------------------- HDR -> SDR

def _hdr_to_linear(x: np.ndarray, kind: str) -> np.ndarray:
    """Map PQ / HLG signals to SDR linear where 1.0 = diffuse white (203 nits)."""
    if kind == "pq":
        m1, m2, c1, c2, c3 = 0.1593017578125, 78.84375, 0.8359375, 18.8515625, 18.6875
        p = np.power(np.clip(x, 0, 1), 1 / m2)
        nits = 10000 * np.power(np.maximum(p - c1, 0) / (c2 - c3 * p), 1 / m1)
    else:
        a, b, c = 0.17883277, 0.28466892, 0.55991073
        x = np.clip(x, 0, 1)
        scene = np.where(x <= 0.5, x * x / 3, (np.exp((x - c) / a) + b) / 12)
        nits = 1000 * np.power(scene, 1.2)
    return (nits / 203).astype(np.float32)


def _tonemap(lin: np.ndarray) -> np.ndarray:
    """Soft roll-off of highlights above diffuse white (keeps colour ratios)."""
    y = np.maximum(lin @ _LUMA.astype(np.float32), 1e-6)
    knee = 0.8
    mapped = np.where(y <= knee, y, knee + (1 - knee) * np.tanh((y - knee) / (1 - knee)))
    return lin * (mapped / y)[..., None]


# ---------------------------------------------------------------- main conversion

def _y_to_lstar(y):
    return np.where(y > 216 / 24389, 116 * np.cbrt(y) - 16, y * 24389 / 27)


def _lstar_to_y(l):
    return np.where(l > 8, ((l + 16) / 116) ** 3, l * 27 / 24389)


def _chroma_reach(lin: np.ndarray):
    """Each pixel = grey(Y) + chroma d. s = how far d reaches relative to the sRGB
    boundary in that direction (s > 1 means out of gamut). Closed form:
    s = max(max(d) / (1 - Y), -min(d) / Y)."""
    y = np.clip(lin @ _LUMA.astype(np.float32), 1e-6, 1 - 1e-6)
    d = lin - y[..., None]
    s = np.maximum(d.max(axis=-1) / (1 - y), -d.min(axis=-1) / y)
    return y, d, s


def gamut_limit(lin_sample: np.ndarray) -> float:
    """The photo's most saturated colour (99.9th pct of the out-of-gamut ones)."""
    _, _, s = _chroma_reach(lin_sample)
    over = s[s > 1.0 + 1e-4]
    return float(np.percentile(over, 99.9)) if over.size else 1.0


def compress_gamut(lin: np.ndarray, s_max: float | None = None, knee: float = 0.8) -> np.ndarray:
    """Pull out-of-gamut colours inside sRGB, keeping luminance and hue.

    Chroma reach above `knee` is remapped with a smooth curve (slope 1 at the
    knee) so the photo's most saturated colour lands exactly on the boundary:
    gradients stay smooth and distinct instead of clipping into flat patches.
    """
    if s_max is None:
        s_max = gamut_limit(lin)
    if s_max <= 1.0 + 1e-4:
        return np.clip(lin, 0, 1)
    y, d, s = _chroma_reach(lin)
    a = s_max - knee
    limit = 1 / (1 / (1 - knee) - 1 / a)
    x = np.maximum(s - knee, 0)
    s_new = np.minimum(np.where(s > knee, knee + x / (1 + x / limit), s), 1.0)
    scale = np.where(s > 1e-6, s_new / np.maximum(s, 1e-6), 1.0)
    return np.clip(y[..., None] + d * scale[..., None], 0, 1)


def srgb_encode(lin: np.ndarray) -> np.ndarray:
    lin = np.clip(lin, 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055)


def _to_linear_srgb(pixels, cs, brightness, saturation, monochrome):
    lin = np.empty(pixels.shape, dtype=np.float32)
    for i, curve in enumerate(cs.curves):
        lin[..., i] = curve.decode(pixels[..., i].astype(np.float32))
    if cs.hdr:
        lin = _hdr_to_linear(lin, cs.hdr)
    if not cs.is_srgb():
        lin = lin @ (_XYZ_TO_LINEAR_SRGB @ cs.matrix).astype(np.float32).T
    if cs.hdr:
        lin = _tonemap(lin)
    if not (brightness or saturation != 1.0 or monochrome):
        return lin
    y = np.maximum(lin @ _LUMA.astype(np.float32), 0)
    if brightness:
        exponent = 1 / (1 + 0.08 * brightness)
        l_new = 100 * np.power(np.clip(_y_to_lstar(y), 0, 100) / 100, exponent)
        y_new = _lstar_to_y(l_new).astype(np.float32)
        lin = lin * np.where(y > 1e-6, y_new / np.maximum(y, 1e-6), 1.0)[..., None]
        y = y_new
    if monochrome:
        return np.repeat(y[..., None], 3, axis=-1)
    if saturation != 1.0:
        lin = y[..., None] + (lin - y[..., None]) * saturation
    return lin


def to_print_srgb(pixels: np.ndarray, cs: ColorSpace, *, gamut: str = "compress",
                  brightness: float = 1.0, saturation: float = 1.0,
                  monochrome: bool = False, chunk_rows: int = 256) -> np.ndarray:
    """pixels: HxWx3 float32 encoded values 0..1 in `cs`. Returns sRGB-encoded float32.

    brightness: print compensation. Paper reflects light, a screen emits it, so an
    untouched print looks darker than the phone. 0 = none, 1 = mild (default),
    2 = strong. Implemented as a lift of the L* midtones: black and white stay put,
    colour ratios are kept.

    Works in row chunks (bounded memory); the gamut limit is measured once on a
    sample of the whole photo so every chunk is mapped identically.
    """
    args = (cs, brightness, saturation, monochrome)
    s_max = None
    if gamut == "compress":
        step = max(1, int(np.sqrt(pixels.shape[0] * pixels.shape[1] / 250_000)))
        s_max = gamut_limit(_to_linear_srgb(pixels[::step, ::step], *args))
    out = np.empty(pixels.shape, np.float32)
    for r in range(0, pixels.shape[0], chunk_rows):
        lin = _to_linear_srgb(pixels[r:r + chunk_rows], *args)
        lin = compress_gamut(lin, s_max) if gamut == "compress" else np.clip(lin, 0, 1)
        out[r:r + chunk_rows] = srgb_encode(lin)
    return out


def to_uint8(encoded: np.ndarray, dither: bool = True, seed: int = 0) -> np.ndarray:
    """Quantise with +/-0.5 LSB noise so smooth skies do not band."""
    h, w = encoded.shape[:2]
    out = np.empty(encoded.shape, np.uint8)
    rows = min(h, 128)
    noise = (np.random.default_rng(seed).uniform(-0.5, 0.5, (rows,) + encoded.shape[1:])
             .astype(np.float32) if dither else np.zeros((rows,) + encoded.shape[1:], np.float32))
    for r in range(0, h, rows):
        block = encoded[r:r + rows] * 255 + noise[:min(rows, h - r)]
        out[r:r + rows] = np.clip(np.rint(block), 0, 255)
    return out
