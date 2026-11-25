"""Encode a directory as ZIP/Base64, optionally split into numbered local TXT files."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import zipfile

DEFAULT_BLOCK_LIMIT = 500_000
MANIFEST = "manifest.json"


def encode_directory(source: Path) -> tuple[str, str]:
    source = source.resolve()
    if not source.is_dir():
        raise ValueError(f"Directory not found: {source}")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for item in sorted(source.rglob("*")):
            if item.is_symlink():
                continue
            rel = item.relative_to(source).as_posix()
            if item.is_dir() and not any(item.iterdir()):
                zf.writestr(rel + "/", b"")
            elif item.is_file():
                zf.write(item, rel)
    data = buffer.getvalue()
    return base64.b64encode(data).decode("ascii"), hashlib.sha256(data).hexdigest()


def write_splits(payload: str, folder: Path, block_limit: int, zip_sha256: str) -> None:
    if block_limit <= 0:
        raise ValueError("--block-limit must be greater than zero")
    if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
        raise ValueError(f"Not a regular directory: {folder}")

    # Protect existing unrelated files. Only numbered TXT and our manifest may be replaced.
    if folder.exists():
        unexpected = [
            item.name for item in folder.iterdir()
            if not (item.is_file() and not item.is_symlink() and
                    (item.name == MANIFEST or
                     (item.suffix == ".txt" and item.stem.isdecimal() and int(item.stem) > 0)))
        ]
        if unexpected:
            raise ValueError(f"Refusing to clean folder with unrelated entries: {unexpected}")

    folder.mkdir(parents=True, exist_ok=True)
    for item in folder.iterdir():
        item.unlink()

    parts = [payload[i:i + block_limit] for i in range(0, len(payload), block_limit)]
    for index, part in enumerate(parts, 1):
        (folder / f"{index}.txt").write_text(part, encoding="ascii")
    metadata = {
        "format": "archiver-splits-v1",
        "parts": len(parts),
        "block_limit": block_limit,
        "characters": len(payload),
        "base64_sha256": hashlib.sha256(payload.encode("ascii")).hexdigest(),
        "zip_sha256": zip_sha256,
    }
    (folder / MANIFEST).write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Created {len(parts)} parts in {folder} ({len(payload)} Base64 characters total)")
    print(f"Part sizes: {', '.join(str(len(part)) for part in parts)} characters")


def main() -> None:
    ap = argparse.ArgumentParser(description="Directory → ZIP → Base64 TXT or numbered local files")
    ap.add_argument("source", type=Path)
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--output", type=Path, help="Single TXT output (default: decoded/encoded.txt)")
    group.add_argument("--splits", nargs="?", type=Path, const=Path("decoded/splits"),
                       metavar="DIR", help="Write 1.txt, 2.txt, ... to DIR (default: decoded/splits/)")
    ap.add_argument("--block-limit", type=int, default=DEFAULT_BLOCK_LIMIT,
                    help=f"Characters per part in --splits mode (default: {DEFAULT_BLOCK_LIMIT})")
    args = ap.parse_args()
    if args.block_limit <= 0:
        ap.error("--block-limit must be positive")
    if args.splits is None and args.block_limit != DEFAULT_BLOCK_LIMIT:
        ap.error("--block-limit requires --splits")

    payload, checksum = encode_directory(args.source)
    if args.splits is not None:
        folder = args.splits.resolve()
        source = args.source.resolve()
        if folder == source or folder.is_relative_to(source):
            ap.error("Split directory must be outside the source directory")
        try:
            write_splits(payload, folder, args.block_limit, checksum)
        except (OSError, ValueError) as exc:
            ap.error(str(exc))
    else:
        output = args.output or Path("decoded/encoded.txt")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="ascii")
        print(f"Created {output} ({len(payload)} Base64 characters)")

    print(f"ZIP SHA-256: {checksum}")


if __name__ == "__main__":
    main()
