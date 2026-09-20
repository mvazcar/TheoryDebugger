"""Create a standalone source ZIP from an explicit allowlist, without Git history."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = {"README.md", "LICENSE", "UNLICENSE", "THIRD_PARTY_NOTICES.md", "CONTRIBUTING.md", ".gitignore", "pyproject.toml",
         "requirements.txt", "lean-toolchain", "lakefile.toml", "lake-manifest.json",
         "TheoryDebugger.lean"}
DIRECTORIES = {"TheoryDebugger", "src", "lean-tests", "tests", "examples",
               "docs", "demo", "scripts", ".github", "contributions"}
SUFFIXES = {".lean", ".py", ".md", ".json", ".txt", ".yml", ".patch"}


def source_files(root=ROOT):
    for name in sorted(FILES):
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Missing or nonregular release input: {name}")
        yield path
    for name in sorted(DIRECTORIES):
        folder = root / name
        if folder.is_symlink():
            raise ValueError(f"Symlinked release directory: {name}")
        for path in sorted(folder.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"Symlinked release input: {path}")
            generated = any(part == "__pycache__" or part.endswith(".egg-info") for part in path.parts)
            if path.is_file() and path.suffix in SUFFIXES and not generated:
                yield path


def build(output, root=ROOT):
    output = Path(output).resolve()
    if output.suffix != ".zip":
        raise ValueError("Output must be a new .zip file")
    files = list(source_files(root))
    # Reject file or directory aliases that collapse on case-insensitive systems.
    spellings = {}
    for path in files:
        parts = path.relative_to(root).parts
        for length in range(1, len(parts) + 1):
            name = "/".join(parts[:length])
            previous = spellings.setdefault(name.casefold(), name)
            if previous != name:
                raise ValueError(f"Case-colliding release paths: {previous}, {name}")
    manifest = {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, "TheoryDebugger/" + path.relative_to(root).as_posix())
        archive.writestr("TheoryDebugger/RELEASE-MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    return {"path": str(output), "files": len(files), "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output")
    print(json.dumps(build(parser.parse_args().output), indent=2))
