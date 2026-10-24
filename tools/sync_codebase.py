"""Synchronize a complete tracked runtime snapshot without changing original source.
Run at repository root: python tools/sync_codebase.py
"""
from pathlib import Path
import subprocess, shutil, hashlib, json

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "repository codebase" / "10_full_runtime_snapshot"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    files = [Path(x.decode("utf-8")) for x in raw.split(b"\0") if x]
    config = {"requirements.txt", "Procfile", "render.yaml", "runtime.txt", "pyproject.toml", "package.json", "package-lock.json"}
    selected = sorted(p for p in files if (p.parts[0] == "src" or p.as_posix() in config)
                      and p.name not in {".env", ".env.local", ".env.production", "credentials.json"}
                      and p.suffix not in {".pem", ".key"} and (ROOT / p).is_file())
    if Path("src/main.py") not in selected:
        raise RuntimeError("Missing src/main.py; refusing to replace archive")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    entries = []
    for p in selected:
        target = OUT / p
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / p, target)
        if digest(ROOT / p) != digest(target):
            raise RuntimeError(f"Mismatch: {p}")
        entries.append({"path": p.as_posix(), "sha256": digest(target)})
    (OUT / "MANIFEST.json").write_text(json.dumps({"count": len(entries), "files": entries}, indent=2), encoding="utf-8")
    actual = {p.relative_to(OUT).as_posix() for p in OUT.rglob("*") if p.is_file() and p.name != "MANIFEST.json"}
    expected = {p.as_posix() for p in selected}
    if actual != expected:
        raise RuntimeError(f"Missing: {expected-actual}; unexpected: {actual-expected}")
    print(f"PASS: {len(entries)} source/config files copied and verified. Originals unchanged.")

if __name__ == "__main__":
    main()
