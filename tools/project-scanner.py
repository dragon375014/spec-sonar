#!/usr/bin/env python3
"""project-scanner.py — generate project-fingerprint.md from any codebase.

Standard library only (os, re, ast, argparse, pathlib, collections).
Python 3.9+. Output is capped at --max-kb (default 20).

Usage:
    python project-scanner.py [ROOT] [-o scan/project-fingerprint.md] [--max-kb 20]
"""
from __future__ import annotations

import argparse
import ast
import os
import re
from collections import Counter
from pathlib import Path

IGNORE_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
    "env", "dist", "build", ".next", ".nuxt", "out", "coverage", ".idea",
    ".vscode", "vendor", "target", ".cache", ".pytest_cache", ".mypy_cache",
    ".tox", "eggs", "site-packages",
}
CODE_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue",
             ".sql", ".prisma", ".go", ".rb", ".java", ".cs", ".php"}
MAX_FILE_BYTES = 512 * 1024

TODO_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b[:\s]*(.{0,70})")
JS_IMPORT_RE = re.compile(
    r"""(?:^|\s)(?:import\s+(?:[\w*{},\s]+?\s+from\s+)?|require\s*\(\s*)["']([^"']+)["']""",
    re.M)
JS_EXPORT_RE = re.compile(
    r"export\s+(?:default\s+)?(?:async\s+)?"
    r"(function|class|const|interface|type)\s+([A-Za-z_$][\w$]*)")
ROUTE_RE = re.compile(
    r"""\b(?:app|router|server|api)\s*\.\s*(get|post|put|patch|delete|all)"""
    r"""\s*\(\s*["'`]([^"'`]+)["'`]""")
PY_ROUTE_RE = re.compile(
    r"""@\s*\w+\.(?:route|get|post|put|patch|delete)\s*\(\s*["']([^"']+)["']""")
SOCKET_ON_RE = re.compile(r"""\.\s*on\s*\(\s*["'`]([\w:./ -]{2,40})["'`]""")
SOCKET_EMIT_RE = re.compile(
    r"""\.\s*(?:emit|broadcast\.emit)\s*\(\s*["'`]([\w:./ -]{2,40})["'`]""")
TS_IFACE_RE = re.compile(
    r"(?:export\s+)?interface\s+([A-Z]\w*)[^{]*\{([^}]*)\}", re.S)
PRISMA_MODEL_RE = re.compile(r"\bmodel\s+(\w+)\s*\{([^}]*)\}", re.S)
SQL_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"']?(\w+)", re.I)


def read_text(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames
                             if d not in IGNORE_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            yield Path(dirpath) / name


def build_tree(root: Path, max_depth: int, max_entries: int) -> list:
    lines, count = [], [0]

    def walk(d: Path, prefix: str, depth: int):
        if depth > max_depth or count[0] >= max_entries:
            return
        try:
            entries = sorted(d.iterdir(),
                             key=lambda p: (p.is_file(), p.name.lower()))
        except OSError:
            return
        entries = [e for e in entries
                   if e.name not in IGNORE_DIRS and not e.name.startswith(".")]
        for e in entries:
            if count[0] >= max_entries:
                lines.append(prefix + "... (truncated)")
                return
            lines.append(f"{prefix}{e.name}{'/' if e.is_dir() else ''}")
            count[0] += 1
            if e.is_dir():
                walk(e, prefix + "  ", depth + 1)

    walk(root, "", 1)
    return lines


def py_signature(fn) -> str:
    a = fn.args
    names = [x.arg for x in getattr(a, "posonlyargs", []) + a.args]
    if a.vararg:
        names.append("*" + a.vararg.arg)
    names += [x.arg for x in a.kwonlyargs]
    if a.kwarg:
        names.append("**" + a.kwarg.arg)
    return f"({', '.join(names)})"


def scan(root: Path) -> dict:
    r = {
        "ext_counter": Counter(), "loc": 0,
        "interfaces": [],          # "path :: symbol"
        "imports_external": Counter(), "imports_internal": [],
        "routes": [], "socket_on": Counter(), "socket_emit": Counter(),
        "models": [], "todos": [], "todo_counter": Counter(),
        "skipped": 0,
    }
    local_names = set()
    for p in iter_files(root):
        if p.suffix in CODE_EXTS:
            local_names.add(p.stem)

    for p in iter_files(root):
        ext = p.suffix.lower()
        if ext not in CODE_EXTS:
            continue
        text = read_text(p)
        if not text:
            r["skipped"] += 1
            continue
        rel = p.relative_to(root).as_posix()
        r["ext_counter"][ext] += 1
        r["loc"] += text.count("\n") + 1

        for i, line in enumerate(text.splitlines(), 1):
            for tag, msg in TODO_RE.findall(line):
                r["todo_counter"][tag] += 1
                if len(r["todos"]) < 40:
                    r["todos"].append(f"{rel}:{i} [{tag}] {msg.strip()}")

        if ext == ".py":
            try:
                tree = ast.parse(text)
            except SyntaxError:
                r["skipped"] += 1
                continue
            for node in tree.body:
                if isinstance(node, ast.Import):
                    for n in node.names:
                        top = n.name.split(".")[0]
                        r["imports_external"][top] += 1
                elif isinstance(node, ast.ImportFrom):
                    top = (node.module or ".").split(".")[0]
                    if node.level or top in local_names:
                        r["imports_internal"].append(
                            f"{rel} -> {node.module or '.'}")
                    else:
                        r["imports_external"][top] += 1
                elif isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(
                        n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    r["interfaces"].append(
                        f"{rel} :: class {node.name}"
                        + (f"  [{', '.join(methods[:8])}]" if methods else ""))
                    fields = [t.target.id for t in node.body
                              if isinstance(t, ast.AnnAssign)
                              and isinstance(t.target, ast.Name)]
                    if fields:
                        r["models"].append(
                            f"{node.name} ({rel}): {', '.join(fields[:12])}")
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    r["interfaces"].append(
                        f"{rel} :: def {node.name}{py_signature(node)}")
            for path_ in PY_ROUTE_RE.findall(text):
                r["routes"].append(f"(py) {path_}  [{rel}]")

        elif ext in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue"}:
            for spec in JS_IMPORT_RE.findall(text):
                if spec.startswith((".", "/")):
                    r["imports_internal"].append(f"{rel} -> {spec}")
                else:
                    r["imports_external"][spec.split("/")[0]] += 1
            for kind, name in JS_EXPORT_RE.findall(text):
                r["interfaces"].append(f"{rel} :: export {kind} {name}")
            for method, path_ in ROUTE_RE.findall(text):
                r["routes"].append(f"{method.upper():6} {path_}  [{rel}]")
            for ev in SOCKET_ON_RE.findall(text):
                r["socket_on"][ev] += 1
            for ev in SOCKET_EMIT_RE.findall(text):
                r["socket_emit"][ev] += 1
            for name, body in TS_IFACE_RE.findall(text):
                fields = re.findall(r"^\s*(\w+)\??\s*:", body, re.M)
                r["models"].append(
                    f"interface {name} ({rel}): {', '.join(fields[:12])}")

        elif ext == ".prisma":
            for name, body in PRISMA_MODEL_RE.findall(text):
                fields = re.findall(r"^\s*(\w+)\s+\w+", body, re.M)
                r["models"].append(
                    f"model {name} ({rel}): {', '.join(fields[:12])}")
        elif ext == ".sql":
            for name in SQL_TABLE_RE.findall(text):
                r["models"].append(f"table {name} ({rel})")
    return r


def render(root: Path, r: dict, caps: dict) -> str:
    out = []
    w = out.append
    w(f"# Project Fingerprint: {root.name}")
    w("")
    w("> generated by project-scanner.py (stdlib-only). "
      "Input for spec-sonar Audit Mode.")
    w("")
    w("## 1. Overview")
    exts = ", ".join(f"{e}:{n}" for e, n in r["ext_counter"].most_common())
    w(f"- code files: {sum(r['ext_counter'].values())} ({exts})")
    w(f"- total LOC: {r['loc']}  |  files skipped (size/parse): {r['skipped']}")
    w("")
    w(f"## 2. Directory Tree (depth<={caps['tree_depth']})")
    w("```")
    out.extend(build_tree(root, caps["tree_depth"], caps["tree_entries"]))
    w("```")
    w("")
    w("## 3. Module Interfaces")
    for line in r["interfaces"][:caps["interfaces"]]:
        w(f"- {line}")
    if len(r["interfaces"]) > caps["interfaces"]:
        w(f"- ... +{len(r['interfaces']) - caps['interfaces']} more (truncated)")
    w("")
    w("## 4. Import Dependencies")
    w("external: " + ", ".join(
        f"{m}({n})" for m, n in r["imports_external"].most_common(30)))
    w("")
    w("internal edges:")
    for line in r["imports_internal"][:caps["internal"]]:
        w(f"- {line}")
    if len(r["imports_internal"]) > caps["internal"]:
        w(f"- ... +{len(r['imports_internal']) - caps['internal']} more")
    w("")
    w("## 5. API Routes & Realtime Events")
    for line in sorted(set(r["routes"]))[:caps["routes"]]:
        w(f"- {line}")
    if r["socket_on"] or r["socket_emit"]:
        w("- socket.on: " + ", ".join(sorted(r["socket_on"])[:40]))
        w("- socket.emit: " + ", ".join(sorted(r["socket_emit"])[:40]))
    w("")
    w("## 6. Data Model Signatures")
    for line in r["models"][:caps["models"]]:
        w(f"- {line}")
    w("")
    w("## 7. TODO / FIXME")
    w("counts: " + (", ".join(
        f"{t}:{n}" for t, n in r["todo_counter"].most_common()) or "none"))
    for line in r["todos"][:caps["todos"]]:
        w(f"- {line}")
    w("")
    w("## 8. Scanner Notes")
    w(f"- caps applied: {caps}")
    w("- regex-based JS/TS extraction: routes/events are best-effort, "
      "verify before trusting as ground truth.")
    return "\n".join(out)


LEVELS = [
    dict(tree_depth=4, tree_entries=200, interfaces=200, internal=80,
         routes=80, models=60, todos=40),
    dict(tree_depth=3, tree_entries=120, interfaces=120, internal=40,
         routes=50, models=40, todos=20),
    dict(tree_depth=2, tree_entries=60, interfaces=60, internal=20,
         routes=30, models=25, todos=10),
]


def main():
    p = argparse.ArgumentParser(description="Generate project-fingerprint.md")
    p.add_argument("root", nargs="?", default=".")
    p.add_argument("-o", "--output", default="project-fingerprint.md")
    p.add_argument("--max-kb", type=int, default=20)
    a = p.parse_args()
    root = Path(a.root).resolve()
    data = scan(root)
    text = ""
    for caps in LEVELS:
        text = render(root, data, caps)
        if len(text.encode("utf-8")) <= a.max_kb * 1024:
            break
    else:
        budget = a.max_kb * 1024 - 60
        text = text.encode("utf-8")[:budget].decode("utf-8", "ignore") \
            + "\n\n...(hard-truncated at size cap)"
    out = Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out} ({len(text.encode('utf-8')) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
