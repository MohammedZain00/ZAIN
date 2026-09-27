"""Run: python -m pytest tests -q   (from the photo-print folder)"""
import io
import struct
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import numpy as np
import pytest
from PIL import Image, ImageCms

from photoprint import color, imaging, ipp, printing


# ---------------------------------------------------------------- helpers

def make_icc(primaries, white=color.D65_xy, name="Display P3") -> bytes:
    """Tiny ICC v2 matrix/TRC profile with an sRGB-shaped parametric curve."""
    m = color.primaries_matrix(primaries, white)
    s15 = lambda v: struct.pack(">i", int(round(v * 65536)))
    xyz = lambda v: b"XYZ \0\0\0\0" + b"".join(s15(c) for c in v)
    para = (b"para\0\0\0\0" + struct.pack(">HH", 3, 0) +
            b"".join(s15(v) for v in (2.4, 1 / 1.055, 0.055 / 1.055, 1 / 12.92, 0.04045)))
    desc_txt = name.encode() + b"\0"
    desc = b"desc\0\0\0\0" + struct.pack(">I", len(desc_txt)) + desc_txt + b"\0" * 79
    tags = [(b"desc", desc), (b"wtpt", xyz(color.D50_XYZ)), (b"rXYZ", xyz(m[:, 0])),
            (b"gXYZ", xyz(m[:, 1])), (b"bXYZ", xyz(m[:, 2])),
            (b"rTRC", para), (b"gTRC", para), (b"bTRC", para), (b"cprt", b"text\0\0\0\0none\0")]
    off, table, body = 132 + 12 * len(tags), b"", b""
    for sig, data in tags:
        while (off + len(body)) % 4:
            body += b"\0"
        table += struct.pack(">4sII", sig, off + len(body), len(data))
        body += data
    size = off + len(body)
    header = (struct.pack(">I", size) + b"lcms" + b"\x02\x10\0\0" + b"mntrRGB XYZ " + b"\0" * 12 +
              b"acsp" + b"APPL" + b"\0" * 4 + b"\0" * 8 + b"\0" * 8 + b"\0" * 4 +
              b"".join(s15(v) for v in color.D50_XYZ) + b"\0" * 48)
    return header + struct.pack(">I", len(tags)) + table + body


P3_ICC = make_icc(color.P3_PRIMARIES)


def p3_image(rgb=(40, 200, 90)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (60, 40), rgb).save(buf, "JPEG", quality=100, subsampling=0, icc_profile=P3_ICC)
    return buf.getvalue()


# ---------------------------------------------------------------- colour

def test_icc_parser_reads_display_p3():
    cs = color.from_icc(P3_ICC)
    assert cs.name == "Display P3"
    assert np.allclose(cs.matrix, color.DISPLAY_P3.matrix, atol=1e-4)
    assert not cs.is_srgb()
    assert color.from_icc(ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()).is_srgb()


def test_p3_to_srgb_matches_littlecms_for_in_gamut_colours():
    """Our numpy path must agree with LittleCMS (the reference CMM) inside the gamut."""
    rng = np.random.default_rng(1)
    src = rng.integers(60, 200, (32, 32, 3)).astype(np.uint8)
    src[..., :] = (src.astype(float) * 0.5 + 64).astype(np.uint8)  # keep it well inside sRGB
    ours = color.to_uint8(color.to_print_srgb(src.astype(np.float32) / 255, color.from_icc(P3_ICC),
                                              brightness=0), dither=False)
    ref = np.asarray(ImageCms.profileToProfile(
        Image.fromarray(src), ImageCms.ImageCmsProfile(io.BytesIO(P3_ICC)),
        ImageCms.createProfile("sRGB"), renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC))
    assert np.abs(ours.astype(int) - ref.astype(int)).max() <= 2


def test_srgb_passthrough_is_lossless():
    x = np.linspace(0, 1, 256, dtype=np.float32)
    img = np.stack([x, x[::-1], np.full_like(x, 0.5)], -1)[None]
    out = color.to_print_srgb(img, color.SRGB, brightness=0)
    assert np.abs(out - img).max() < 1e-3


def test_gamut_compression_keeps_hue_and_order():
    """Saturated P3 reds of rising chroma must stay distinct (clipping would merge them)."""
    ramp = np.linspace(0.3, 1.0, 50, dtype=np.float32)
    img = np.stack([np.ones_like(ramp), 1 - ramp, 1 - ramp], -1)[None]  # P3 pink -> pure red
    comp = color.to_print_srgb(img, color.DISPLAY_P3, brightness=0)[0]
    clip = color.to_print_srgb(img, color.DISPLAY_P3, brightness=0, gamut="clip")[0]
    assert comp.min() >= 0 and comp.max() <= 1
    assert np.all(np.diff(comp[:, 1]) <= 1e-6)            # still monotonic
    assert len(np.unique(np.round(comp * 255), axis=0)) > len(np.unique(np.round(clip * 255), axis=0))


def test_brightness_lifts_midtones_but_keeps_black_and_white():
    img = np.array([[[0, 0, 0], [0.5, 0.5, 0.5], [1, 1, 1]]], np.float32)
    out = color.to_print_srgb(img, color.SRGB, brightness=1)
    assert out[0, 0].max() < 1e-4 and out[0, 2].min() > 0.999
    assert 0.51 < out[0, 1, 0] < 0.56


def test_hdr_pq_is_tonemapped_into_range():
    cs = color.from_nclx({"color_primaries": 9, "transfer_characteristics": 16})
    assert cs.hdr == "pq"
    img = np.full((2, 2, 3), 0.9, np.float32)   # ~4000 nits highlight
    out = color.to_print_srgb(img, cs)
    assert 0.9 < out.max() <= 1.0


# ---------------------------------------------------------------- decoding

def test_load_jpeg_with_p3_profile():
    ph = imaging.load(p3_image(), "iphone.jpg")
    assert ph.colorspace.name == "Display P3" and ph.size == (60, 40)


def test_load_heic_10bit_with_icc_and_nclx():
    pillow_heif = pytest.importorskip("pillow_heif")
    grad = (np.linspace(0, 1023, 64 * 48 * 3).reshape(48, 64, 3).astype(np.uint16) << 6)
    hf = pillow_heif.from_bytes(mode="RGB;16", size=(64, 48), data=grad.tobytes())
    buf = io.BytesIO()
    hf.save(buf, quality=-1, icc_profile=P3_ICC)
    ph = imaging.load(buf.getvalue(), "IMG_0001.HEIC")
    assert ph.fmt == "HEIF" and ph.bit_depth == 10 and ph.pixels.dtype == np.uint16
    assert ph.colorspace.name == "Display P3"
    buf = io.BytesIO()
    pillow_heif.from_bytes(mode="RGB", size=(8, 8), data=bytes(192)).save(buf)
    assert "sRGB" in imaging.load(buf.getvalue(), "a.heic").colorspace.name  # nclx path


def test_exif_orientation_and_alpha():
    im = Image.new("RGBA", (40, 20), (255, 0, 0, 0))
    exif = Image.Exif()
    exif[0x0112] = 6  # rotate 90
    buf = io.BytesIO()
    im.save(buf, "PNG", exif=exif)
    ph = imaging.load(buf.getvalue(), "x.png")
    assert ph.size == (20, 40)
    assert ph.pixels[0, 0].tolist() == [255, 255, 255]  # transparent -> white paper


def test_16bit_png():
    arr = (np.linspace(0, 65535, 100).reshape(10, 10)).astype(np.uint16)
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, "PNG")
    ph = imaging.load(buf.getvalue(), "g.png")
    assert ph.bit_depth == 16 and ph.pixels.shape == (10, 10, 3)


# ---------------------------------------------------------------- layout & output

def test_render_4x6_borderless_fill_exact_size_and_rotation():
    ph = imaging.load(p3_image(), "wide.jpg")           # landscape photo
    s = imaging.PrintSettings(paper="4x6", borderless=True, dpi=300)
    pages, dpi, paper = imaging.render_pages([ph], s)
    assert pages[0].size == (1200, 1800)               # portrait page, no white edge
    assert pages[0].getpixel((0, 0)) != (255, 255, 255)


def test_grid_layout_and_margins():
    photos = [imaging.load(p3_image((i * 40, 90, 200 - i * 30)), f"{i}.jpg") for i in range(5)]
    s = imaging.PrintSettings(paper="A4", layout="4", borderless=False, fit="fit", dpi=150)
    pages, _, _ = imaging.render_pages(photos, s)
    assert len(pages) == 2
    assert pages[0].getpixel((2, 2)) == (255, 255, 255)  # margin stays paper-white


def test_pdf_is_well_formed():
    ph = imaging.load(p3_image(), "a.jpg")
    pages, dpi, paper = imaging.render_pages([ph, ph], imaging.PrintSettings(layout="1", dpi=100))
    pdf = imaging.encode_pdf(pages, dpi, paper)
    assert pdf.startswith(b"%PDF-1.4") and pdf.rstrip().endswith(b"%%EOF")
    assert b"/Count 2" in pdf and b"/MediaBox [0 0 288.0000 432.0000]" in pdf
    xref = int(pdf.rsplit(b"startxref\n", 1)[1].split(b"\n")[0])
    assert pdf[xref:xref + 4] == b"xref"


# ---------------------------------------------------------------- IPP against a fake printer

class FakePrinter(BaseHTTPRequestHandler):
    jobs = []

    def log_message(self, *a):
        pass

    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        op = struct.unpack(">H", body[2:4])[0]
        rid = struct.unpack(">I", body[4:8])[0]
        if op == ipp.GET_PRINTER_ATTRS:
            db = [ipp.Col({"media-size": ipp.Col({"x-dimension": 10160, "y-dimension": 15240}),
                           "media-top-margin": 0, "media-bottom-margin": 0,
                           "media-left-margin": 0, "media-right-margin": 0}),
                  ipp.Col({"media-size": ipp.Col({"x-dimension": 21000, "y-dimension": 29700}),
                           "media-top-margin": 300, "media-bottom-margin": 300,
                           "media-left-margin": 300, "media-right-margin": 300})]
            attrs = [("printer-make-and-model", "HP Smart Tank 580-590 series", ipp.TEXT),
                     ("printer-state", 3, ipp.ENUM),
                     ("document-format-supported", ["application/pdf", "image/jpeg"], ipp.MIMETYPE),
                     ("media-col-database", db, None),
                     ("media-type-supported", ["stationery", "photographic-glossy", "com.hp.advanced-photo"], ipp.KEYWORD),
                     ("media-top-margin-supported", [0, 300], ipp.INTEGER),
                     ("print-quality-supported", [3, 4, 5], ipp.ENUM),
                     ("marker-names", ["Black", "Tri-color"], ipp.NAME),
                     ("marker-levels", [80, 65], ipp.INTEGER),
                     ("marker-colors", ["#000000", "#00FFFF#FF00FF#FFFF00"], ipp.NAME)]
            groups = [(ipp.OPERATION_GROUP, [("attributes-charset", "utf-8", ipp.CHARSET)]),
                      (ipp.PRINTER_GROUP, attrs)]
        else:
            status, request = ipp.decode_response(b"\x02\x00\x00\x00" + body[4:])
            FakePrinter.jobs.append((op, request, body))
            groups = [(ipp.OPERATION_GROUP, [("attributes-charset", "utf-8", ipp.CHARSET)]),
                      (ipp.JOB_GROUP, [("job-id", 42, ipp.INTEGER), ("job-state", 3, ipp.ENUM)])]
        resp = bytearray(ipp.encode_request(0, rid, groups))
        self.send_response(200)
        self.send_header("Content-Type", "application/ipp")
        self.send_header("Content-Length", str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)


@pytest.fixture()
def fake_printer():
    srv = HTTPServer(("127.0.0.1", 0), FakePrinter)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    FakePrinter.jobs.clear()
    yield f"ipp://127.0.0.1:{srv.server_port}/ipp/print"
    srv.shutdown()


def test_capabilities_parse_collections(fake_printer):
    caps = printing.capabilities(fake_printer)
    assert caps["model"].startswith("HP Smart Tank")
    assert (10160, 15240) in caps["borderless_sizes"] and (21000, 29700) not in caps["borderless_sizes"]
    assert caps["markers"][1] == {"name": "Tri-color", "level": 65, "color": "#00FFFF#FF00FF#FFFF00"}


def test_print_job_sends_photo_settings(fake_printer):
    s = imaging.PrintSettings(paper="4x6", media_type="glossy", quality="best", copies=2, dpi=150)
    res = printing.print_photos([imaging.load(p3_image(), "a.jpg")], s, fake_printer)
    assert res["jobs"][0]["job_id"] == 42
    assert res["warnings"] == ["a.jpg: only ~10 ppi at this size; it may look soft."]
    op, req, body = FakePrinter.jobs[0]
    assert op == ipp.PRINT_JOB
    job = ipp.flatten(req["job"][0])
    assert job["copies"] == 2 and job["print-quality"] == 5 and job["print-scaling"] == "none"
    assert job["media-col"]["media-type"] == "com.hp.advanced-photo"   # HP's own photo keyword wins
    assert job["media-col"]["media-size"] == {"x-dimension": 10160, "y-dimension": 15240}
    assert job["media-col"]["media-top-margin"] == 0
    assert b"%PDF-1.4" in body


def test_borderless_falls_back_when_printer_lacks_it(fake_printer):
    s = imaging.PrintSettings(paper="A4", borderless=True, dpi=72)
    res = printing.print_photos([imaging.load(p3_image(), "a.jpg")], s, fake_printer)
    assert any("borderless" in w for w in res["warnings"])
    job = ipp.flatten(FakePrinter.jobs[0][1]["job"][0])
    assert job["media-col"]["media-top-margin"] == 300
