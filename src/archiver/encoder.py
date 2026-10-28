"""Encode a directory as one ZIP/Base64 text file; standard library only."""
import argparse
import base64
import hashlib
import io
from pathlib import Path
import zipfile


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


def main() -> None:
    ap = argparse.ArgumentParser(description="Directory → ZIP → one Base64 TXT")
    ap.add_argument("source", type=Path)
    ap.add_argument("--output", type=Path, default=Path("encoded.txt"))
    args = ap.parse_args()
    payload, checksum = encode_directory(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="ascii")
    print(f"Created {args.output} ({len(payload)} Base64 characters)")
    print(f"ZIP SHA-256: {checksum}")


if __name__ == "__main__":
    main()
