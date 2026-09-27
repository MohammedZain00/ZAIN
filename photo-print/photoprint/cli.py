"""Command line: python -m photoprint <command> ...   (run with no command to open the app)"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import imaging, ipp, printing


def _settings(a) -> imaging.PrintSettings:
    extra = dict(kv.split("=", 1) for kv in a.ipp or [])
    return imaging.PrintSettings(
        paper=a.paper, media_type=a.media, quality=a.quality, borderless=not a.border,
        fit="fit" if a.fit else "fill", layout=a.layout, copies=a.copies,
        color_mode=a.color, dpi=a.dpi, brightness=a.brightness, saturation=a.saturation,
        sharpen=a.sharpen, gamut=a.gamut, auto_rotate=not a.no_rotate,
        margin_mm=a.margin, media_source=a.source, extra=extra)


def _add_job_options(p):
    p.add_argument("files", nargs="+", help="photos: HEIC, JPG, PNG, TIFF, WebP, AVIF, RAW...")
    p.add_argument("--paper", default="4x6", help=f"{', '.join(imaging.PAPERS)} or WxHmm")
    p.add_argument("--media", default="glossy", help="glossy | matte | brochure | plain | auto | <ipp keyword>")
    p.add_argument("--quality", default="best", choices=["draft", "normal", "best"])
    p.add_argument("--border", action="store_true", help="white border (default: borderless)")
    p.add_argument("--fit", action="store_true", help="show the whole photo instead of filling the paper")
    p.add_argument("--layout", default="1", help="photos per page: 1,2,4,6,9... or CxR")
    p.add_argument("--copies", type=int, default=1)
    p.add_argument("--color", default="color", choices=["color", "monochrome", "mono-black"],
                   help="monochrome = neutral B&W photo with all inks; mono-black = black ink only")
    p.add_argument("--dpi", type=int, default=0, help="0 = auto (300/600)")
    p.add_argument("--brightness", type=float, default=1.0, help="print compensation 0..2 (default 1)")
    p.add_argument("--saturation", type=float, default=1.0)
    p.add_argument("--sharpen", type=float, default=1.0, help="0..2")
    p.add_argument("--gamut", default="compress", choices=["compress", "clip"])
    p.add_argument("--no-rotate", action="store_true")
    p.add_argument("--margin", type=float, default=3.0, help="mm, with --border")
    p.add_argument("--source", default="auto", help="paper tray (media-source)")
    p.add_argument("--ipp", action="append", metavar="NAME=VALUE", help="extra raw IPP job attribute")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="photoprint", description="Faithful photo printing for HP Smart Tank 580")
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("printers", help="find printers on the network / this computer")
    p = sub.add_parser("info", help="show everything the printer supports (+ ink levels)")
    p.add_argument("printer")
    p = sub.add_parser("print", help="print photos")
    p.add_argument("-p", "--printer", required=True, help="ipp://IP/ipp/print, an IP, cups:NAME or windows:NAME")
    _add_job_options(p)
    p = sub.add_parser("convert", help="save print-ready files (PDF or JPEGs) without printing")
    p.add_argument("-o", "--out", default="print-ready", help="folder, or a .pdf path")
    _add_job_options(p)
    p = sub.add_parser("jobs", help="list pending jobs")
    p.add_argument("printer")
    p = sub.add_parser("cancel", help="cancel a job")
    p.add_argument("printer")
    p.add_argument("job_id", type=int)
    p = sub.add_parser("app", help="open the app in the browser (default)")
    p.add_argument("--port", type=int, default=8631)
    p.add_argument("--no-browser", action="store_true")

    a = ap.parse_args(argv)
    try:
        if a.cmd in (None, "app"):
            from . import web
            web.serve(getattr(a, "port", 8631), open_browser=not getattr(a, "no_browser", False))
        elif a.cmd == "printers":
            found = printing.discover()
            if not found:
                print("No printer found. Make sure the printer is on the same Wi-Fi, then use its IP:\n"
                      "  printer panel > Wi-Fi icon > IP address, e.g.  -p 192.168.1.50")
            for pr in found:
                print(f"{pr['name']:<40} {pr['uri']}")
        elif a.cmd == "info":
            print(json.dumps(printing.capabilities(a.printer), indent=2, ensure_ascii=False))
        elif a.cmd == "print":
            res = printing.print_photos(a.files, _settings(a), a.printer)
            _report(res)
        elif a.cmd == "convert":
            s = _settings(a)
            photos = [imaging.load(f) for f in a.files]
            pages, dpi, paper = imaging.render_pages(photos, s)
            if a.out.lower().endswith(".pdf"):
                with open(a.out, "wb") as f:
                    f.write(imaging.encode_pdf(pages, dpi, paper))
                print(f"saved {a.out} ({len(pages)} pages, {dpi} dpi, {paper.label})")
            else:
                os.makedirs(a.out, exist_ok=True)
                for i, pg in enumerate(pages, 1):
                    stem = os.path.splitext(photos[i - 1].name)[0] if len(pages) == len(photos) else f"page-{i}"
                    path = os.path.join(a.out, f"{stem}-print.jpg")
                    with open(path, "wb") as f:
                        f.write(imaging.encode_jpeg(pg, dpi))
                    print(f"saved {path} ({pg.width}x{pg.height}, {dpi} dpi, sRGB)")
        elif a.cmd == "jobs":
            for j in ipp.IPPPrinter(a.printer).jobs():
                print(j)
        elif a.cmd == "cancel":
            ipp.IPPPrinter(a.printer).cancel(a.job_id)
            print("cancelled")
    except (ipp.IPPError, OSError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def _report(res: dict):
    for ph in res["photos"]:
        print(f"  {ph['name']}: {ph['format']} {ph['width']}x{ph['height']} "
              f"{ph['bit_depth']}-bit, {ph['colorspace']} -> sRGB")
    print(f"sent {res['pages']} page(s) on {res['paper']} at {res['dpi']} dpi: {res.get('jobs')}")
    for w in res["warnings"]:
        print("warning:", w)
