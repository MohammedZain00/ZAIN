---
name: file-to-markdown
description: Convert any document to Markdown with anydoc before reading it. Use whenever the user wants to read, summarize, review, translate, search, or extract data from a .docx/.doc/.pdf/.pptx/.ppt/.xlsx/.xls/.odt/.ods/.odp/.rtf/.epub/.csv file - whether it is in the project, was uploaded, or was just downloaded. Triggers in Arabic too - "اقرأ الملف", "اقرأ ملف الوورد", "لخص الـ PDF", "حوّل الملف لماركداون", "استخرج الجدول من الملف", "راجع العرض التقديمي". Never open these formats with Read or cat directly - convert first, then read the Markdown.
---

# Read any document as Markdown

Binary office formats (`.docx`, `.pdf`, `.pptx`, `.xlsx`, ...) are ZIP archives or
byte streams. Reading one with `Read` or `cat` gives mojibake, a wall of XML, or
nothing. Always convert to Markdown first, then read the Markdown.

The converter is [anydoc](https://github.com/firecrawl/anydoc) - a Rust document
pipeline that detects the format from file *content* (not the extension), parses
it, and serializes GitHub-Flavored Markdown. It keeps headings, bold/italic,
nested lists, tables (including merged cells), footnotes, links, and equations as
LaTeX. Typical document: a few milliseconds.

## The one command

```bash
.claude/skills/file-to-markdown/scripts/to-md.sh <file-or-dir>...
```

It prints the path of each `.md` it produced - `report.docx` becomes
`report.docx.md`, keeping the source extension so a `.docx` and a `.pdf` of the
same report never collide. Then read that `.md` with `Read`.

Useful flags:

| Flag | Effect |
| --- | --- |
| `--outdir DIR` | Where the `.md` files go (default: `$TMPDIR/md-cache`) |
| `--ocr` | Send scanned PDF pages to Firecrawl Parse (needs `FIRECRAWL_API_KEY`) |
| `--force` | Re-convert even if a fresh `.md` is already cached |
| `--stdout` | Print the Markdown instead of writing a file |

Given a directory it walks it, converts every supported document inside, and
stays quiet about everything else.

Pass `--outdir` pointed at the session scratchpad so converted files never land
in the user's repo. Only write the `.md` into the project itself when the user
asks for the Markdown as a deliverable.

## Workflow

1. **Locate the file.** Uploads usually land under `/mnt/user-data/uploads` or the
   session scratchpad; project files are where the user says. If unsure, `ls` the
   likely directories rather than guessing a path.
2. **Convert.** Run the script on the file (or on a whole directory - it walks it
   and converts every supported document it finds).
3. **Read the Markdown** it printed. For a long document, don't dump the whole
   thing: `wc -l` it first, then `grep -n '^#'` for the outline and `sed -n` the
   sections you actually need.
4. **Cite by heading**, not by page - Markdown has no page numbers. Say "under
   *Payment Terms*", not "on page 4".

Each converted file starts with a provenance comment:

```
<!-- anydoc: converted from /abs/path/report.docx (mtime 1758...) -->
```

The script uses it to skip re-converting an unchanged source, so calling it
repeatedly in a session is cheap.

## Supported formats

| Family | Extensions |
| --- | --- |
| Word | `.doc` `.docx` `.docm` `.dotx` |
| Presentations | `.ppt` `.pptx` `.pptm` `.ppsx` `.potx` |
| Spreadsheets | `.xls` `.xlsx` `.xlsm` `.xlsb` |
| OpenDocument | `.odt` `.ods` `.odp` |
| Other | `.pdf` `.rtf` `.epub` `.csv` |

Spreadsheets become one Markdown table per sheet; presentations become one
section per slide, with speaker notes.

## Scanned PDFs

A PDF whose pages are images has no text layer. anydoc exits with code **3** and
the script reports `NEEDS OCR`. anydoc does no OCR itself - two options:

- Re-run with `--ocr` (routes the document through Firecrawl Parse; needs
  `FIRECRAWL_API_KEY` in the environment, otherwise it tries keyless).
- Tell the user the PDF is a scan and ask whether to send it to the hosted OCR
  service, since that uploads the document off the machine. **Ask before sending
  anything that looks confidential.**

## Formats anydoc does not take

Don't force these through the script:

- `.md`, `.txt`, `.json`, `.yaml`, `.xml`, source code → already text, just `Read`.
- `.html` → `Read` it, or strip tags if it's huge.
- Images (`.png`, `.jpg`, ...) → the `Read` tool sees images directly.
- `.pages`, `.numbers`, `.key` → Apple iWork; ask the user to export to Office or
  PDF first.
- `.eml`, `.msg` → parse with Python's `email` module.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `anydoc: io error` | Wrong path. `ls` the directory; watch for spaces in names. |
| Exit code 3 / `NEEDS OCR` | Scanned PDF - see above. |
| Exit code 1 | File is corrupt or truncated. Check `ls -la` size and `file` output. |
| Exit code 2 | Bad flag, or `--format` names a format anydoc doesn't have. |
| First run is slow | `npx` is downloading the package. `npm i -g @firecrawl/anydoc` makes later runs instant. |
| No network for npx | `pip install firecrawl-anydoc`, then `python3 -c "import anydoc,sys;print(anydoc.to_markdown(sys.argv[1]))" FILE`. |
| Table looks wrong | Merged cells flatten. Open the source in the right app if the exact layout matters. |

## Installing this skill globally

It lives in this repo, so it loads for sessions in this project. To get it in
every project on a machine:

```bash
cp -r .claude/skills/file-to-markdown ~/.claude/skills/
```
