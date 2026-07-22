#!/usr/bin/env python3
"""Read-only scan for duplicate, merge, and wikilink candidates in a Markdown/Obsidian vault.

Usage:
  OBSIDIAN_VAULT_PATH=/path/to/vault python scan_merge_link_candidates.py
  python scan_merge_link_candidates.py /path/to/vault
  INCLUDE_TRASH=1 python scan_merge_link_candidates.py /path/to/vault
  python scan_merge_link_candidates.py /path/to/vault --include-trash

By default the scanner excludes `.trash`. Use `INCLUDE_TRASH=1` or `--include-trash` only when the user explicitly asks to clean trash-like stubs.

Writes /tmp/obsidian_note_scan.json and prints a concise summary.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import math
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

DEFAULT_EXCLUDE_DIRS = {".git", ".obsidian", "node_modules", ".stfolder", ".sync"}
FRONT_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
CODE_RE = re.compile(r"```.*?```", re.S)
INLINE_CODE_RE = re.compile(r"`[^`]+`")
WIKILINK_RE = re.compile(r"!?\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
TAG_RE = re.compile(r"(?<!\w)#([A-Za-z0-9_/-]+)")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+.#'/-]*")
STOP = set("""
a an the and or but if then else for from to of in on at by with without into onto over under after before during while when where why how what who whom whose which this that these those there here is are was were be been being am do does did done have has had having can could should would may might must will shall as not no yes it its itself we us our ours you your yours they them their theirs he him his she her hers i me my mine about above across again against all almost also although always among amongst another any anybody anyone anything anyhow anywhere apart around because become becomes becoming became between both each either every everybody everyone everything few first further get gets got just last least less many more most mostly much myself new next other others own per perhaps put quite rather same since some somebody someone something somewhat sometimes still such than through too very via well within yet note notes todo todos task tasks journal daily weekly monthly year month day today yesterday tomorrow thing things stuff link links linked source sources article articles book books page pages section sections chapter chapters quote quotes idea ideas thinking thoughts think read reading write writing make makes made one two three example examples use used using want wants need needs project projects plan plans review reviews meeting work works
""".split())


def norm_title(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    s = re.sub(r"^(\d{4}[-_ ]\d{2}[-_ ]\d{2}|\d{8}|\d{4}[-_ ]\d{2}|\d+)[ -_]+", "", s)
    return re.sub(r"\s+", " ", s)


def strip_frontmatter(txt: str) -> tuple[str, str]:
    m = FRONT_RE.match(txt)
    return (txt[m.end():], m.group(1)) if m else (txt, "")


def parse_aliases(front: str) -> list[str]:
    aliases: list[str] = []
    lines = front.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^aliases\s*:", line):
            rest = line.split(":", 1)[1].strip()
            if rest.startswith("[") and rest.endswith("]"):
                aliases += [x.strip().strip("\"'") for x in rest.strip("[]").split(",") if x.strip()]
            elif rest:
                aliases.append(rest.strip("\"'"))
            else:
                j = i + 1
                while j < len(lines) and re.match(r"^\s+-\s+", lines[j]):
                    aliases.append(re.sub(r"^\s+-\s+", "", lines[j]).strip().strip("\"'"))
                    j += 1
    return aliases


def parse_id(front: str) -> str | None:
    m = re.search(r"^id:\s*(.+?)\s*$", front, re.M)
    return m.group(1).strip().strip("\"'") if m else None


def tokenize(txt: str) -> list[str]:
    txt = CODE_RE.sub(" ", txt)
    txt = INLINE_CODE_RE.sub(" ", txt)
    txt = WIKILINK_RE.sub(lambda m: " " + m.group(1) + " ", txt)
    toks = []
    for m in WORD_RE.finditer(txt):
        w = m.group(0).lower().strip("'/-")
        if len(w) < 3 or w in STOP or re.fullmatch(r"\d+", w):
            continue
        toks.append(w)
    return toks


def title_tokens(title: str) -> list[str]:
    return [w for w in norm_title(title).split() if w not in STOP and len(w) > 1]


def linked_between(a: dict, b: dict) -> bool:
    bnames = {b["title"], Path(b["path"]).with_suffix("").as_posix(), *b["aliases"]}
    anames = {a["title"], Path(a["path"]).with_suffix("").as_posix(), *a["aliases"]}
    return bool(a["links"] & bnames or b["links"] & anames)


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    include_trash = _truthy(os.environ.get("INCLUDE_TRASH"))
    vault_arg = None
    for arg in sys.argv[1:]:
        if arg == "--include-trash":
            include_trash = True
        elif vault_arg is None:
            vault_arg = arg
        else:
            raise SystemExit(f"Unexpected argument: {arg}")

    vault = Path(vault_arg or os.environ.get("OBSIDIAN_VAULT_PATH", os.getcwd())).expanduser().resolve()
    exclude_dirs = set(DEFAULT_EXCLUDE_DIRS)
    if not include_trash:
        exclude_dirs.add(".trash")

    notes = []
    for p in vault.rglob("*.md"):
        rel_path = p.relative_to(vault)
        if any(part in exclude_dirs for part in rel_path.parts):
            continue
        txt = p.read_text(encoding="utf-8", errors="ignore")
        body, front = strip_frontmatter(txt)
        aliases = parse_aliases(front)
        tokens = tokenize(body)
        notes.append({
            "path": rel_path.as_posix(),
            "title": p.stem,
            "aliases": aliases,
            "id": parse_id(front),
            "raw_hash": hashlib.sha256(txt.encode()).hexdigest(),
            "body_hash": hashlib.sha256(body.encode()).hexdigest(),
            "body": body,
            "words": len(WORD_RE.findall(body)),
            "links": set(WIKILINK_RE.findall(txt)),
            "tags": set(TAG_RE.findall(txt)),
            "tokens": tokens,
            "tf": Counter(tokens),
            "title_tokens": title_tokens(p.stem) + sum((title_tokens(a) for a in aliases), []),
        })

    n = len(notes)
    df = Counter()
    for note in notes:
        df.update(set(note["tokens"]))
    vocab = {t for t, c in df.items() if 2 <= c <= max(2, int(n * 0.45))}
    for note in notes:
        vec = {t: (1 + math.log(c)) * math.log((n + 1) / (df[t] + 0.5)) for t, c in note["tf"].items() if t in vocab}
        note["vec"] = vec
        note["vec_norm"] = math.sqrt(sum(v * v for v in vec.values())) or 1.0

    def cosine(a: dict, b: dict) -> float:
        if len(a["vec"]) > len(b["vec"]):
            a, b = b, a
        return sum(v * b["vec"].get(t, 0) for t, v in a["vec"].items()) / (a["vec_norm"] * b["vec_norm"])

    by_raw: dict[str, list[dict]] = defaultdict(list)
    by_body: dict[str, list[dict]] = defaultdict(list)
    by_norm_title: dict[str, list[dict]] = defaultdict(list)
    by_id: dict[str, list[dict]] = defaultdict(list)
    for note in notes:
        by_raw[note["raw_hash"]].append(note)
        by_body[note["body_hash"]].append(note)
        by_norm_title[norm_title(note["title"])].append(note)
        if note["id"]:
            by_id[note["id"]].append(note)

    def groups(mapping):
        return [[x["path"] for x in g] for g in mapping.values() if len(g) > 1]

    pairs = []
    for i, a in enumerate(notes):
        for b in notes[i + 1:]:
            cos = cosine(a, b)
            ta, tb = set(a["title_tokens"]), set(b["title_tokens"])
            title_j = len(ta & tb) / len(ta | tb) if ta or tb else 0.0
            tag_j = len(a["tags"] & b["tags"]) / len(a["tags"] | b["tags"]) if a["tags"] or b["tags"] else 0.0
            shorter = a if a["words"] <= b["words"] else b
            if cos >= 0.36 or title_j >= 0.60 or (shorter["words"] < 160 and cos >= 0.20):
                pairs.append({
                    "a": a["path"],
                    "b": b["path"],
                    "cosine": round(cos, 3),
                    "title_overlap": round(title_j, 3),
                    "tag_overlap": round(tag_j, 3),
                    "linked": linked_between(a, b),
                    "words": [a["words"], b["words"]],
                })
    pairs.sort(key=lambda r: (r["cosine"], r["title_overlap"]), reverse=True)

    patterns = []
    for target in notes:
        for phrase in [target["title"], *target["aliases"]]:
            nt = norm_title(phrase)
            if len(nt) >= 5 and nt not in STOP and not re.fullmatch(r"\d+|\d{4} \d{2} \d{2}", nt):
                patterns.append((target, phrase, re.compile(r"(?<![\w\[])(%s)(?![\w\]])" % re.escape(phrase), re.I)))
    mentions = []
    for src in notes:
        raw_no_links = re.sub(r"\[\[[^\]]+\]\]", " ", src["body"])
        for target, phrase, pat in patterns:
            if src is target or linked_between(src, target):
                continue
            m = pat.search(raw_no_links)
            if m:
                start, end = max(0, m.start() - 70), min(len(raw_no_links), m.end() + 100)
                mentions.append({
                    "source": src["path"],
                    "target": target["path"],
                    "phrase": phrase,
                    "context": " ".join(raw_no_links[start:end].split()),
                })

    report = {
        "vault": str(vault),
        "note_count": n,
        "raw_duplicate_groups": groups(by_raw),
        "body_duplicate_groups": groups(by_body),
        "same_normalized_title_groups": groups(by_norm_title),
        "duplicate_id_groups": groups(by_id),
        "merge_candidates": pairs[:100],
        "explicit_unlinked_mentions": mentions[:150],
    }
    out = Path("/tmp/obsidian_note_scan.json")
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Vault: {vault}")
    print(f"Markdown notes scanned: {n}")
    print(f"Raw duplicate groups: {len(report['raw_duplicate_groups'])}")
    print(f"Body duplicate groups: {len(report['body_duplicate_groups'])}")
    print(f"Same normalized-title groups: {len(report['same_normalized_title_groups'])}")
    print(f"Duplicate ID groups: {len(report['duplicate_id_groups'])}")
    print("\nTop merge candidates:")
    for r in pairs[:25]:
        print(f"  - {r['a']} <-> {r['b']} | cos={r['cosine']} title={r['title_overlap']} linked={r['linked']} words={r['words']}")
    print("\nTop unlinked title mentions:")
    for r in mentions[:25]:
        print(f"  - {r['source']} -> {r['target']} via {r['phrase']!r}; ctx={r['context'][:180]}")
    print(f"\nStructured report: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
