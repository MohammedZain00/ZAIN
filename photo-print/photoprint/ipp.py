"""Small, dependency-free IPP/2.0 client (RFC 8010/8011 + IPP Everywhere / PWG 5100.x).

The HP Smart Tank 580 speaks IPP on ipp://<printer-ip>:631/ipp/print (the same
protocol AirPrint and Mopria use), so we can query its real capabilities
(paper sizes, media types, borderless margins, ink levels) and submit jobs with
photo settings without depending on any OS driver.
"""
from __future__ import annotations

import http.client
import ssl
import struct
from urllib.parse import urlparse

# value tags
INTEGER, BOOLEAN, ENUM = 0x21, 0x22, 0x23
OCTET, DATETIME, RESOLUTION, RANGE = 0x30, 0x31, 0x32, 0x33
BEG_COLLECTION, TEXT_LANG, NAME_LANG, END_COLLECTION = 0x34, 0x35, 0x36, 0x37
TEXT, NAME, KEYWORD, URI, URISCHEME, CHARSET, LANGUAGE, MIMETYPE, MEMBERNAME = (
    0x41, 0x42, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4A)
OUT_OF_BAND = {0x10: "unsupported", 0x12: "unknown", 0x13: "no-value"}
# group tags
OPERATION_GROUP, JOB_GROUP, END_GROUP, PRINTER_GROUP, UNSUPPORTED_GROUP = 1, 2, 3, 4, 5

PRINT_JOB, VALIDATE_JOB, CANCEL_JOB, GET_JOB_ATTRS, GET_JOBS, GET_PRINTER_ATTRS = (
    0x0002, 0x0004, 0x0008, 0x0009, 0x000A, 0x000B)
IDENTIFY_PRINTER = 0x003C

STATUS_TEXT = {0x0000: "successful-ok", 0x0001: "ok-ignored-or-substituted-attributes",
               0x0002: "ok-conflicting-attributes", 0x0400: "client-error-bad-request",
               0x0403: "client-error-forbidden", 0x040A: "client-error-document-format-not-supported",
               0x040B: "client-error-attributes-or-values-not-supported",
               0x0500: "server-error-internal-error", 0x0506: "server-error-not-accepting-jobs",
               0x0507: "server-error-busy"}


class IPPError(RuntimeError):
    pass


class Col(dict):
    """Marks a dict as an IPP collection when encoding."""


def _encode_value(tag: int, value) -> bytes:
    if tag in (INTEGER, ENUM):
        return struct.pack(">i", value)
    if tag == BOOLEAN:
        return b"\x01" if value else b"\x00"
    if tag == RESOLUTION:
        x, y, units = value
        return struct.pack(">iib", x, y, units)
    if tag == RANGE:
        return struct.pack(">ii", *value)
    return value if isinstance(value, bytes) else str(value).encode("utf-8")


def _guess_tag(value) -> int:
    if isinstance(value, bool):
        return BOOLEAN
    if isinstance(value, int):
        return INTEGER
    if isinstance(value, Col):
        return BEG_COLLECTION
    return KEYWORD


def _encode_attr(name: str, values, tag: int | None = None) -> bytes:
    if not isinstance(values, (list, tuple)) or (tag in (RESOLUTION, RANGE) and
                                                  isinstance(values[0], int)):
        values = [values]
    out = b""
    for i, v in enumerate(values):
        t = tag or _guess_tag(v)
        n = name.encode() if i == 0 else b""
        if t == BEG_COLLECTION:
            out += struct.pack(">BH", t, len(n)) + n + struct.pack(">H", 0)
            for member, mv in v.items():
                mtag = None
                if isinstance(mv, tuple) and len(mv) == 2 and isinstance(mv[0], int) and mv[0] > 0x0F:
                    mtag, mv = mv
                mb = member.encode()
                out += struct.pack(">BHH", MEMBERNAME, 0, len(mb)) + mb
                out += _encode_attr("", mv, mtag)
            out += struct.pack(">BHH", END_COLLECTION, 0, 0)
        else:
            data = _encode_value(t, v)
            out += struct.pack(">BH", t, len(n)) + n + struct.pack(">H", len(data)) + data
    return out


def encode_request(op: int, request_id: int, groups: list[tuple[int, list]]) -> bytes:
    """groups: [(group_tag, [(name, value, tag_or_None), ...]), ...]"""
    out = struct.pack(">BBHI", 2, 0, op, request_id)
    for gtag, attrs in groups:
        out += bytes([gtag])
        for name, value, tag in attrs:
            out += _encode_attr(name, value, tag)
    return out + bytes([END_GROUP])


def _decode_value(tag: int, data: bytes):
    if tag in (INTEGER, ENUM):
        return struct.unpack(">i", data)[0]
    if tag == BOOLEAN:
        return data != b"\x00"
    if tag == RESOLUTION:
        return struct.unpack(">iib", data)
    if tag == RANGE:
        return struct.unpack(">ii", data)
    if tag in OUT_OF_BAND:
        return None
    if tag in (TEXT_LANG, NAME_LANG):
        ln = struct.unpack(">H", data[:2])[0]
        tl = struct.unpack(">H", data[2 + ln:4 + ln])[0]
        return data[4 + ln:4 + ln + tl].decode("utf-8", "replace")
    if tag == OCTET or tag == DATETIME:
        return data
    return data.decode("utf-8", "replace")


def decode_response(data: bytes) -> tuple[int, dict]:
    """Returns (status, {group_name: [ {attr: [values]} , ...]})."""
    if len(data) < 8:
        raise IPPError("empty IPP response")
    status = struct.unpack(">H", data[2:4])[0]
    pos, groups, current, last = 8, {}, None, None
    stack: list = []  # collection nesting: (dict, pending_member_name)
    names = {1: "operation", 2: "job", 4: "printer", 5: "unsupported"}
    while pos < len(data):
        tag = data[pos]
        pos += 1
        if tag == END_GROUP:
            break
        if tag < 0x10:
            current = {}
            groups.setdefault(names.get(tag, str(tag)), []).append(current)
            continue
        nlen = struct.unpack(">H", data[pos:pos + 2])[0]
        name = data[pos + 2:pos + 2 + nlen].decode("utf-8", "replace")
        pos += 2 + nlen
        vlen = struct.unpack(">H", data[pos:pos + 2])[0]
        raw = data[pos + 2:pos + 2 + vlen]
        pos += 2 + vlen
        if stack:  # inside a collection
            col, member = stack[-1]
            if tag == MEMBERNAME:
                stack[-1] = (col, raw.decode())
            elif tag == END_COLLECTION:
                stack.pop()
            elif tag == BEG_COLLECTION:
                new = {}
                col.setdefault(member, []).append(new)
                stack.append((new, None))
            else:
                col.setdefault(member, []).append(_decode_value(tag, raw))
            continue
        target = current if current is not None else {}
        if name:
            last = name
            target[name] = []
        if tag == BEG_COLLECTION:
            new = {}
            target.setdefault(last, []).append(new)
            stack.append((new, None))
        else:
            target.setdefault(last, []).append(_decode_value(tag, raw))
    return status, groups


def flatten(values: list):
    """Collection members come back as single-element lists; unwrap them."""
    if isinstance(values, list) and len(values) == 1:
        values = values[0]
    if isinstance(values, dict):
        return {k: flatten(v) for k, v in values.items()}
    if isinstance(values, list):
        return [flatten(v) if isinstance(v, (dict, list)) else v for v in values]
    return values


class IPPPrinter:
    def __init__(self, uri: str, timeout: float = 30, user: str = "photoprint"):
        if "://" not in uri:
            uri = f"ipp://{uri}/ipp/print"
        self.uri = uri
        u = urlparse(uri)
        self.secure = u.scheme in ("ipps", "https")
        self.host, self.port = u.hostname, u.port or (443 if u.scheme == "https" else 631)
        self.path = u.path or "/ipp/print"
        self.timeout, self.user, self._rid = timeout, user, 0

    def _op_attrs(self, extra=()):
        return [("attributes-charset", "utf-8", CHARSET),
                ("attributes-natural-language", "en", LANGUAGE),
                ("printer-uri", self.uri.replace("https://", "ipps://").replace("http://", "ipp://"), URI),
                ("requesting-user-name", self.user, NAME), *extra]

    def request(self, op: int, op_attrs=(), job_attrs=(), document: bytes = b"") -> dict:
        self._rid += 1
        groups = [(OPERATION_GROUP, self._op_attrs(op_attrs))]
        if job_attrs:
            groups.append((JOB_GROUP, list(job_attrs)))
        body = encode_request(op, self._rid, groups) + document
        if self.secure:
            # Printers use self-signed certificates on the local network.
            ctx = ssl.create_default_context()
            ctx.check_hostname, ctx.verify_mode = False, ssl.CERT_NONE
            conn = http.client.HTTPSConnection(self.host, self.port, timeout=self.timeout, context=ctx)
        else:
            conn = http.client.HTTPConnection(self.host, self.port, timeout=self.timeout)
        try:
            conn.request("POST", self.path, body, {"Content-Type": "application/ipp"})
            resp = conn.getresponse()
            data = resp.read()
            if resp.status != 200:
                raise IPPError(f"HTTP {resp.status} {resp.reason} from printer")
        finally:
            conn.close()
        status, groups = decode_response(data)
        if status >= 0x0400:
            msg = groups.get("operation", [{}])[0].get("status-message", [""])[0]
            unsupported = groups.get("unsupported", [{}])[0]
            raise IPPError(f"{STATUS_TEXT.get(status, hex(status))} {msg} "
                           f"{'unsupported: ' + ', '.join(unsupported) if unsupported else ''}".strip())
        return {"status": status, "status_text": STATUS_TEXT.get(status, hex(status)), **groups}

    def attributes(self, requested=("all", "media-col-database")) -> dict:
        r = self.request(GET_PRINTER_ATTRS, [("requested-attributes", list(requested), KEYWORD)])
        return r.get("printer", [{}])[0]

    def print_job(self, document: bytes, doc_format: str, job_name: str, job_attrs: list) -> dict:
        r = self.request(PRINT_JOB, [("job-name", job_name, NAME),
                                     ("document-format", doc_format, MIMETYPE)],
                         job_attrs, document)
        job = r.get("job", [{}])[0]
        return {"job_id": (job.get("job-id") or [None])[0],
                "state": (job.get("job-state") or [None])[0],
                "status": r["status_text"]}

    def jobs(self) -> list[dict]:
        r = self.request(GET_JOBS, [("which-jobs", "not-completed", KEYWORD),
                                    ("requested-attributes", ["job-id", "job-name", "job-state",
                                                              "job-state-reasons"], KEYWORD)])
        return [{k: v[0] if len(v) == 1 else v for k, v in j.items()} for j in r.get("job", [])]

    def cancel(self, job_id: int) -> None:
        self.request(CANCEL_JOB, [("job-id", int(job_id), INTEGER)])

    def identify(self) -> None:
        self.request(IDENTIFY_PRINTER, [("identify-actions", ["display", "sound"], KEYWORD)])
