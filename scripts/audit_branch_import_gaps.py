"""Branch integrity audit: for every .py file TRACKED on this git branch, parse its
top-level local imports (same-repo modules, not stdlib/third-party) and check whether the
imported module is ALSO tracked on this branch. This is exactly the class of bug found with
fal_vertical.py (opportunity_suggestion_engine.py, tracked, silently depended on an untracked
working-tree copy). Never modifies anything -- read-only audit, prints a report.
"""
from __future__ import annotations

import ast
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def tracked_files() -> set[str]:
    out = subprocess.run(["git", "ls-files", "*.py"], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    return set(out.stdout.splitlines())


def local_module_names(tracked: set[str]) -> dict[str, str]:
    """Map importable module name -> its tracked file path, for root-level and src/-rooted modules."""
    mapping = {}
    for path in tracked:
        p = Path(path)
        if p.name == "__init__.py":
            continue
        if len(p.parts) == 1:
            mapping[p.stem] = path
        elif p.parts[0] == "src" and len(p.parts) == 3:
            mapping[p.stem] = path  # src/<pkg>/<mod>.py -> importable as <pkg>.<mod>, but also bare mod name in sys.path-hacked scripts
    return mapping


def parse_local_imports(file_path: Path, known_modules: set[str]) -> set[str]:
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8", errors="replace"), filename=str(file_path))
    except SyntaxError:
        return set()
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                top = node.module.split(".")[0]
                if top in known_modules:
                    found.add(top)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in known_modules:
                    found.add(top)
    return found


def main() -> None:
    tracked = tracked_files()
    mod_map = local_module_names(tracked)
    known_modules = set(mod_map.keys())

    problems = []
    checked = 0
    for rel_path in sorted(tracked):
        if rel_path.startswith("data/") or "/backups/" in rel_path or rel_path.startswith(".claude/"):
            continue
        checked += 1
        abs_path = REPO_ROOT / rel_path
        imports = parse_local_imports(abs_path, known_modules)
        for mod in imports:
            target_file = mod_map[mod]
            if target_file not in tracked:
                problems.append((rel_path, mod, target_file))  # shouldn't happen given mod_map built from tracked, sanity only

    print(f"Checked {checked} tracked .py files against {len(known_modules)} known local module names.")
    print(f"NOTE: this only catches 'imports a module name that ALSO exists untracked but under "
          f"a different resolvable path' style bugs indirectly -- the real fal_vertical.py bug was "
          f"'imports a module whose ONLY copy is untracked'. Checking that class directly below.\n")

    # Second, more direct check: does the import resolve at all when running from a clean
    # perspective (i.e. is the module name only satisfiable by an UNTRACKED file sitting in the
    # working tree)? We approximate this by listing untracked .py files at repo root / src and
    # cross-referencing against imports made by tracked files.
    untracked_out = subprocess.run(
        ["git", "status", "--porcelain", "--ignored=no"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    untracked_py = {
        line[3:] for line in untracked_out.stdout.splitlines()
        if line.startswith("??") and line[3:].endswith(".py") and "/" not in line[3:].strip("./")
    }
    untracked_root_modules = {Path(f).stem: f for f in untracked_py if Path(f).parent == Path(".")}

    real_gaps = []
    for rel_path in sorted(tracked):
        if rel_path.startswith("data/") or "/backups/" in rel_path or rel_path.startswith(".claude/"):
            continue
        abs_path = REPO_ROOT / rel_path
        try:
            tree = ast.parse(abs_path.read_text(encoding="utf-8", errors="replace"), filename=str(abs_path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            mod = None
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                mod = node.module.split(".")[0]
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    m = alias.name.split(".")[0]
                    if m in untracked_root_modules and m not in known_modules:
                        real_gaps.append((rel_path, m, untracked_root_modules[m]))
                continue
            if mod and mod in untracked_root_modules and mod not in known_modules:
                real_gaps.append((rel_path, mod, untracked_root_modules[mod]))

    print(f"=== REAL GAPS: tracked file imports a module whose ONLY copy is untracked ===")
    if not real_gaps:
        print("None found. (fal_vertical.py was already fixed, so it correctly doesn't show up here.)")
    else:
        for importer, mod, untracked_path in sorted(set(real_gaps)):
            print(f"- {importer} imports `{mod}` -- only found untracked at {untracked_path}")


if __name__ == "__main__":
    main()
