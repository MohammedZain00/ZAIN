#!/usr/bin/env bash
# Convert documents to Markdown with anydoc, caching by source mtime.
# Usage: to-md.sh [--outdir DIR] [--ocr] [--force] [--stdout] <file-or-dir>...
set -uo pipefail

OUTDIR="${MD_OUTDIR:-${TMPDIR:-/tmp}/md-cache}"
OCR=0
FORCE=0
TO_STDOUT=0
INPUTS=()

usage() {
  sed -n '2,4p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --outdir) OUTDIR="${2:-}"; [ -n "$OUTDIR" ] || { echo "to-md: --outdir needs a path" >&2; exit 2; }; shift 2 ;;
    --ocr)    OCR=1; shift ;;
    --force)  FORCE=1; shift ;;
    --stdout) TO_STDOUT=1; shift ;;
    -h|--help) usage 0 ;;
    --) shift; INPUTS+=("$@"); break ;;
    -*) echo "to-md: unknown option $1" >&2; usage 2 ;;
    *)  INPUTS+=("$1"); shift ;;
  esac
done

[ ${#INPUTS[@]} -gt 0 ] || { echo "to-md: no input given" >&2; usage 2; }

# Prefer a globally installed binary; fall back to npx (slow first run).
if command -v anydoc >/dev/null 2>&1; then
  ANYDOC=(anydoc)
elif command -v npx >/dev/null 2>&1; then
  ANYDOC=(npx -y @firecrawl/anydoc)
else
  echo "to-md: neither 'anydoc' nor 'npx' is on PATH." >&2
  echo "       Install with: npm i -g @firecrawl/anydoc   (or: pip install firecrawl-anydoc)" >&2
  exit 127
fi

EXTS="doc docx docm dotx ppt pptx pptm ppsx potx xls xlsx xlsm xlsb odt ods odp pdf rtf epub csv"

supported() {
  local ext="${1##*.}"
  ext="$(printf '%s' "$ext" | tr '[:upper:]' '[:lower:]')"
  case " $EXTS " in *" $ext "*) return 0 ;; *) return 1 ;; esac
}

mtime_of() { stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null || echo 0; }

failures=0

convert_one() {
  local src explicit abs base out marker tmp status
  src="$1"
  explicit="${2:-1}"   # 0 when reached by walking a directory
  abs="$(cd "$(dirname "$src")" && pwd)/$(basename "$src")"

  if ! supported "$abs"; then
    # Walking a directory turns up plenty of non-documents; only say so when
    # the user pointed at this file by name.
    [ "$explicit" = 1 ] && echo "SKIP     $abs (not a document anydoc handles - read it directly)" >&2
    return 0
  fi

  if [ "$TO_STDOUT" = 1 ]; then
    "${ANYDOC[@]}" "$abs"
    status=$?
    [ $status -eq 0 ] || report_failure "$abs" $status
    return $status
  fi

  mkdir -p "$OUTDIR" || return 1
  # Keep the source extension in the name: report.docx -> report.docx.md, so a
  # .docx and a .pdf of the same report never fight over one output file.
  base="$(basename "$abs")"
  out="$OUTDIR/$base.md"
  marker="<!-- anydoc: converted from $abs (mtime $(mtime_of "$abs")) -->"

  # Same filename from a different directory must not clobber this one either.
  if [ -e "$out" ] && ! head -n 1 "$out" | grep -qF "from $abs "; then
    out="$OUTDIR/${base%.*}-$(printf '%s' "$abs" | cksum | cut -d" " -f1).${base##*.}.md"
  fi

  if [ "$FORCE" = 0 ] && [ -e "$out" ] && head -n 1 "$out" | grep -qxF "$marker"; then
    echo "CACHED   $out"
    return 0
  fi

  tmp="$out.tmp$$"
  "${ANYDOC[@]}" "$abs" -o "$tmp"
  status=$?
  if [ $status -ne 0 ] && [ $status -eq 3 ] && [ "$OCR" = 1 ]; then
    echo "OCR      $abs (sending to Firecrawl Parse)" >&2
    "${ANYDOC[@]}" "$abs" --ocr hosted -o "$tmp"
    status=$?
  fi

  if [ $status -ne 0 ]; then
    rm -f "$tmp"
    report_failure "$abs" $status
    return $status
  fi

  { printf '%s\n\n' "$marker"; cat "$tmp"; } > "$out" && rm -f "$tmp"
  echo "OK       $out"
}

report_failure() {
  local abs="$1" status="$2"
  failures=$((failures + 1))
  case "$status" in
    3) echo "NEEDS OCR $abs - scanned PDF with no text layer. Re-run with --ocr (uploads the file to Firecrawl Parse; ask the user first)." >&2 ;;
    2) echo "USAGE    $abs - anydoc rejected the invocation." >&2 ;;
    1) echo "FAILED   $abs - unreadable or corrupt." >&2 ;;
    *) echo "FAILED   $abs - anydoc exited $status." >&2 ;;
  esac
}

for input in "${INPUTS[@]}"; do
  if [ -d "$input" ]; then
    while IFS= read -r -d '' f; do
      convert_one "$f" 0
    done < <(find "$input" -type f -not -path '*/.*' -print0)
  elif [ -e "$input" ]; then
    convert_one "$input" 1
  else
    echo "MISSING  $input - no such file. Check the path with ls." >&2
    failures=$((failures + 1))
  fi
done

[ "$failures" -eq 0 ] || exit 1
