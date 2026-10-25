import os
import sys
import json
import ast
import sqlite3

ROOT = os.path.abspath(".")
OUT = os.path.join(ROOT, "docs", "audit", "evidence")

def scan_python_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
        tree = ast.parse(code)
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        lines = len(code.splitlines())
        return {"lines": lines, "classes": classes, "functions": functions, "parse_error": False}
    except Exception as e:
        return {"lines": 0, "classes": [], "functions": [], "parse_error": str(e)}

inventory = {"backend": {}, "frontend": {}, "tests": {}, "docs": {}}

for root, dirs, files in os.walk(os.path.join(ROOT, "backend")):
    if "__pycache__" in root or ".pytest_cache" in root:
        continue
    for f in files:
        if f.endswith(".py"):
            full = os.path.join(root, f)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            inventory["backend"][rel] = scan_python_file(full)

for root, dirs, files in os.walk(os.path.join(ROOT, "src")):
    for f in files:
        if f.endswith((".ts", ".tsx")):
            full = os.path.join(root, f)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            try:
                with open(full, "r", encoding="utf-8", errors="ignore") as fp:
                    lines = len(fp.read().splitlines())
            except Exception:
                lines = 0
            inventory["frontend"][rel] = {"lines": lines}

for root, dirs, files in os.walk(os.path.join(ROOT, "tests")):
    if "__pycache__" in root:
        continue
    for f in files:
        if f.endswith(".py"):
            full = os.path.join(root, f)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            inventory["tests"][rel] = scan_python_file(full)

with open(os.path.join(OUT, "inventory_raw.json"), "w", encoding="utf-8") as f:
    json.dump(inventory, f, indent=2)

print(f"Inventory collected: {len(inventory['backend'])} backend files, {len(inventory['frontend'])} frontend files, {len(inventory['tests'])} benchmark/test files.")
