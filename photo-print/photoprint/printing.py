"""Find the printer, read what it supports, and send the job with the right options."""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import tempfile
import time

from . import imaging, ipp
from .imaging import PrintSettings

QUALITY = {"draft": 3, "normal": 4, "best": 5}
# Friendly media names -> IPP keywords to try, best match first. HP publishes its
# own keywords (com.hp.*) for its papers; generic PWG names are the fallback.
MEDIA_TYPES = {
    "glossy": ["com.hp.advanced-photo", "photographic-glossy", "photographic-high-gloss",
               "com.hp.photographic-glossy", "photographic"],
    "matte": ["photographic-matte", "com.hp.matte-photo", "com.hp.matte-brochure", "photographic"],
    "brochure": ["com.hp.glossy-brochure", "brochure-glossy", "com.hp.matte-brochure"],
    "plain": ["stationery", "com.hp.plain"],
    "auto": ["auto"],
}


# ---------------------------------------------------------------- discovery

def discover(timeout: float = 3.0) -> list[dict]:
    """Network (mDNS/Bonjour) + OS print queues."""
    found: list[dict] = []
    try:
        from zeroconf import ServiceBrowser, Zeroconf

        class Listener:
            def add_service(self, zc, type_, name):
                info = zc.get_service_info(type_, name, 2000)
                if not info or not info.parsed_addresses():
                    return
                props = {k.decode(): (v or b"").decode("utf-8", "ignore")
                         for k, v in info.properties.items()}
                scheme = "ipps" if type_.startswith("_ipps") else "ipp"
                uri = f"{scheme}://{info.parsed_addresses()[0]}:{info.port}/{props.get('rp', 'ipp/print')}"
                found.append({"name": props.get("ty") or name.split(".")[0], "uri": uri,
                              "kind": "ipp"})

            update_service = remove_service = lambda *a: None

        zc = Zeroconf()
        try:
            ServiceBrowser(zc, ["_ipp._tcp.local.", "_ipps._tcp.local."], Listener())
            time.sleep(timeout)
        finally:
            zc.close()
    except ImportError:
        pass
    # one entry per host, prefer plain ipp (faster, no TLS) and HP units first
    seen, unique = set(), []
    for p in sorted(found, key=lambda p: (p["uri"].startswith("ipps"), "HP" not in p["name"])):
        host = p["uri"].split("//")[1].split(":")[0]
        if host not in seen:
            seen.add(host)
            unique.append(p)
    return unique + os_queues()


def os_queues() -> list[dict]:
    out = []
    if platform.system() == "Windows":
        try:
            import win32print
            flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            for p in win32print.EnumPrinters(flags):
                out.append({"name": p[2], "uri": f"windows:{p[2]}", "kind": "windows"})
        except ImportError:
            pass
    elif shutil.which("lpstat"):
        try:
            res = subprocess.run(["lpstat", "-e"], capture_output=True, text=True, timeout=5)
            out += [{"name": q, "uri": f"cups:{q}", "kind": "cups"} for q in res.stdout.split()]
        except (OSError, subprocess.SubprocessError):
            pass
    return out


# ---------------------------------------------------------------- capabilities

def capabilities(uri: str) -> dict:
    """Normalised view of what an IPP printer supports (sizes, media, margins, ink)."""
    if not _is_ipp(uri):
        return {"uri": uri, "kind": uri.split(":")[0], "note": "OS queue: driver decides options"}
    a = ipp.IPPPrinter(uri, timeout=10).attributes()
    g = lambda k, d=None: a.get(k, d if d is not None else [])
    sizes, borderless = [], set()
    for entry in g("media-col-database"):
        e = ipp.flatten(entry)
        size = e.get("media-size", {})
        x, y = size.get("x-dimension"), size.get("y-dimension")
        if isinstance(x, int) and isinstance(y, int):
            sizes.append((x, y))
            if all(e.get(f"media-{s}-margin") == 0 for s in ("top", "bottom", "left", "right")):
                borderless.add((x, y))
    margins = {s: min(g(f"media-{s}-margin-supported", [300]) or [300])
               for s in ("top", "right", "bottom", "left")}
    nonzero = {s: min([m for m in g(f"media-{s}-margin-supported", [300]) if m > 0] or [300])
               for s in ("top", "right", "bottom", "left")}
    markers = [{"name": n, "level": l, "color": c} for n, l, c in
               zip(g("marker-names"), g("marker-levels"), g("marker-colors"))]
    return {
        "uri": uri, "kind": "ipp",
        "model": (g("printer-make-and-model", [""]) or [""])[0],
        "state": {3: "idle", 4: "printing", 5: "stopped"}.get((g("printer-state", [0]) or [0])[0], "?"),
        "state_reasons": g("printer-state-reasons"),
        "formats": g("document-format-supported"),
        "media": g("media-supported"),
        "media_sizes": sorted(set(sizes)),
        "borderless_sizes": sorted(borderless),
        "media_types": g("media-type-supported"),
        "media_sources": g("media-source-supported"),
        "quality": g("print-quality-supported"),
        "color_modes": g("print-color-mode-supported"),
        "sides": g("sides-supported"),
        "scaling": g("print-scaling-supported"),
        "content_optimize": g("print-content-optimize-supported"),
        "resolutions": [f"{x}x{y}dpi" for x, y, _ in g("printer-resolution-supported")],
        "min_margins_hmm": margins, "bordered_margins_hmm": nonzero,
        "copies_max": (g("copies-supported", [(1, 99)]) or [(1, 99)])[0][1],
        "markers": markers,
    }


def _is_ipp(uri: str) -> bool:
    return not uri.startswith(("windows:", "cups:"))


def _pick(wanted: list[str], supported: list[str]) -> str | None:
    if not supported:
        return wanted[0] if wanted else None
    for w in wanted:
        if w in supported:
            return w
    return None


# ---------------------------------------------------------------- job building

def plan_margins(s: PrintSettings, caps: dict | None, paper: imaging.Paper) -> tuple[tuple, list[str]]:
    """Margins (mm: top,right,bottom,left) to lay the page out with, plus warnings."""
    warnings = []
    if s.borderless:
        if caps and caps.get("borderless_sizes") is not None and caps.get("media_sizes"):
            dims = paper.ipp_dims
            ok = any(abs(x - dims[0]) <= 100 and abs(y - dims[1]) <= 100
                     for x, y in caps["borderless_sizes"])
            if not ok:
                warnings.append(f"The printer does not report borderless for {paper.label}; "
                                "printing with its minimum margins instead.")
                m = caps["bordered_margins_hmm"]
                return tuple(m[k] / 100 for k in ("top", "right", "bottom", "left")), warnings
        return (0, 0, 0, 0), warnings
    if caps and caps.get("bordered_margins_hmm"):
        m = caps["bordered_margins_hmm"]
        return tuple(max(m[k] / 100, s.margin_mm) for k in ("top", "right", "bottom", "left")), warnings
    return (s.margin_mm,) * 4, warnings


def ipp_job_attributes(s: PrintSettings, caps: dict | None, paper: imaging.Paper,
                       margins_mm: tuple, doc_format: str) -> tuple[list, list[str]]:
    caps = caps or {}
    notes = []
    x, y = paper.ipp_dims
    if caps.get("media_sizes"):  # snap to the printer's exact size for this paper
        best = min(caps["media_sizes"], key=lambda d: abs(d[0] - x) + abs(d[1] - y))
        if abs(best[0] - x) + abs(best[1] - y) <= 200:
            x, y = best
    top, right, bottom, left = (int(round(m * 100)) for m in margins_mm)
    media_col = {"media-size": ipp.Col({"x-dimension": x, "y-dimension": y}),
                 "media-top-margin": top, "media-bottom-margin": bottom,
                 "media-left-margin": left, "media-right-margin": right}

    wanted = MEDIA_TYPES.get(s.media_type, [s.media_type])
    media_type = _pick(wanted, caps.get("media_types", []))
    if media_type and media_type != "auto":
        media_col["media-type"] = media_type
    elif s.media_type not in ("auto", "plain"):
        notes.append(f"Media type '{s.media_type}' not offered by the printer; using its default.")
    if s.media_source != "auto" and s.media_source in caps.get("media_sources", [s.media_source]):
        media_col["media-source"] = s.media_source

    attrs = [("copies", max(1, int(s.copies)), ipp.INTEGER),
             ("media-col", ipp.Col(media_col), None),
             ("sides", "one-sided", ipp.KEYWORD)]
    q = QUALITY.get(s.quality, 5)
    if not caps.get("quality") or q in caps["quality"]:
        attrs.append(("print-quality", q, ipp.ENUM))
    mode = "monochrome" if s.color_mode == "mono-black" else "color"
    if not caps.get("color_modes") or mode in caps["color_modes"]:
        attrs.append(("print-color-mode", mode, ipp.KEYWORD))
    if not caps.get("content_optimize") or "photo" in caps["content_optimize"]:
        attrs.append(("print-content-optimize", "photo", ipp.KEYWORD))
    # PDF pages are already exactly paper-sized: place 1:1. A bare JPEG is a picture
    # of the whole page, so ask for fill (borderless) / fit (with margins).
    scaling = "none" if doc_format == "application/pdf" else ("fill" if s.borderless else "fit")
    if not caps.get("scaling") or scaling in caps["scaling"]:
        attrs.append(("print-scaling", scaling, ipp.KEYWORD))
    for k, v in s.extra.items():  # expert pass-through, e.g. {"print-rendering-intent": "perceptual"}
        attrs.append((k, v, None))
    return attrs, notes


# ---------------------------------------------------------------- submitting

def print_photos(paths_or_photos, s: PrintSettings, printer_uri: str, *, job_name: str = "Photos",
                 dry_run: bool = False) -> dict:
    photos = [p if isinstance(p, imaging.Photo) else imaging.load(p) for p in paths_or_photos]
    paper = imaging.paper_from(s.paper)
    caps = None
    if _is_ipp(printer_uri) and not dry_run:
        caps = capabilities(printer_uri)
    margins, warnings = plan_margins(s, caps, paper)
    for ph in photos:
        ppi = imaging.effective_ppi(ph, paper, s)
        if ppi < 150:
            warnings.append(f"{ph.name}: only ~{ppi:.0f} ppi at this size; it may look soft.")
    pages, dpi, paper = imaging.render_pages(photos, s, margins)
    result = {"pages": len(pages), "dpi": dpi, "paper": paper.label, "warnings": warnings,
              "photos": [p.describe() for p in photos]}
    if dry_run:
        result["pdf"] = imaging.encode_pdf(pages, dpi, paper)
        return result

    kind = printer_uri.split(":")[0]
    if kind == "windows":
        result["jobs"] = [_print_windows(printer_uri[8:], pages, dpi, paper, s, job_name)]
    elif kind == "cups":
        result["jobs"] = [_print_cups(printer_uri[5:], imaging.encode_pdf(pages, dpi, paper),
                                      paper, s, job_name)]
    else:
        formats = caps.get("formats", []) if caps else []
        printer = ipp.IPPPrinter(printer_uri)
        if not formats or "application/pdf" in formats:
            attrs, notes = ipp_job_attributes(s, caps, paper, margins, "application/pdf")
            result["jobs"] = [printer.print_job(imaging.encode_pdf(pages, dpi, paper),
                                                "application/pdf", job_name, attrs)]
        elif "image/jpeg" in formats:
            attrs, notes = ipp_job_attributes(s, caps, paper, margins, "image/jpeg")
            result["jobs"] = [printer.print_job(imaging.encode_jpeg(pg, dpi), "image/jpeg",
                                                f"{job_name} {i + 1}", attrs)
                              for i, pg in enumerate(pages)]
        else:
            raise ipp.IPPError("Printer accepts neither PDF nor JPEG: " + ", ".join(formats))
        warnings += notes
    return result


def _print_cups(queue: str, pdf: bytes, paper, s: PrintSettings, job_name: str) -> dict:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf)
    media = paper.ipp + (".Borderless" if s.borderless else "")
    opts = {"media": media, "print-quality": str(QUALITY.get(s.quality, 5)),
            "print-color-mode": "monochrome" if s.color_mode == "mono-black" else "color",
            "print-content-optimize": "photo", "print-scaling": "none", "ColorModel": "RGB"}
    mt = MEDIA_TYPES.get(s.media_type, [s.media_type])[0]
    if mt != "auto":
        opts["media-type"] = mt
    cmd = ["lp", "-d", queue, "-n", str(s.copies), "-t", job_name]
    for k, v in opts.items():
        cmd += ["-o", f"{k}={v}"]
    try:
        res = subprocess.run(cmd + [f.name], capture_output=True, text=True, timeout=60)
    finally:
        os.unlink(f.name)
    if res.returncode:
        raise RuntimeError(res.stderr.strip() or "lp failed")
    return {"status": res.stdout.strip()}


def _print_windows(name: str, pages, dpi, paper, s: PrintSettings, job_name: str) -> dict:
    """Windows spooler (USB or any installed driver). The HP driver expects sRGB,
    which is exactly what we produce; borderless = pick the driver's borderless form."""
    import win32con
    import win32gui
    import win32print
    import win32ui
    from PIL import ImageWin

    h = win32print.OpenPrinter(name)
    try:
        info = win32print.GetPrinter(h, 2)
        dm = info["pDevMode"]
        port = info["pPortName"]
        names = win32print.DeviceCapabilities(name, port, win32con.DC_PAPERNAMES)
        codes = win32print.DeviceCapabilities(name, port, win32con.DC_PAPERS)
        dims = win32print.DeviceCapabilities(name, port, win32con.DC_PAPERSIZE)  # 0.1 mm
        best, best_score = None, None
        for n, c, d in zip(names, codes, dims):
            w, hh = (d["x"], d["y"]) if isinstance(d, dict) else d
            size_err = abs(w - paper.w_mm * 10) + abs(hh - paper.h_mm * 10)
            if size_err > 30:
                continue
            is_bl = any(t in n.lower() for t in ("borderless", "بدون حدود", "sans bordure"))
            score = size_err + (0 if is_bl == s.borderless else 1000)
            if best_score is None or score < best_score:
                best, best_score = c, score
        if best is not None:
            dm.PaperSize = best
            dm.Fields |= win32con.DM_PAPERSIZE
        dm.Copies = max(1, int(s.copies))
        dm.Color = 1 if s.color_mode == "mono-black" else 2
        dm.PrintQuality = {"draft": -1, "normal": -3, "best": -4}.get(s.quality, -4)
        dm.Orientation = 1
        if s.media_type in ("glossy", "matte", "brochure"):
            dm.MediaType = 3  # DMMEDIA_GLOSSY; drivers map it to their photo paper
            dm.Fields |= 0x02000000  # DM_MEDIATYPE
        dm.Fields |= (win32con.DM_COPIES | win32con.DM_COLOR | win32con.DM_PRINTQUALITY
                      | win32con.DM_ORIENTATION)
    finally:
        win32print.ClosePrinter(h)

    hdc = win32gui.CreateDC("WINSPOOL", name, dm)
    dc = win32ui.CreateDCFromHandle(hdc)
    phys_w, phys_h = dc.GetDeviceCaps(110), dc.GetDeviceCaps(111)
    off_x, off_y = dc.GetDeviceCaps(112), dc.GetDeviceCaps(113)
    dc.StartDoc(job_name)
    for page in pages:
        dc.StartPage()
        ImageWin.Dib(page).draw(dc.GetHandleOutput(), (-off_x, -off_y, phys_w - off_x, phys_h - off_y))
        dc.EndPage()
    dc.EndDoc()
    dc.DeleteDC()
    return {"status": "sent to Windows spooler", "paper_code": best}
