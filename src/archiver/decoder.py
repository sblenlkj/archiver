"""Decode one Base64 TXT into a ZIP and optionally unpack; stdlib only."""
import argparse
import base64
import binascii
import hashlib
import io
from pathlib import Path, PurePosixPath
import stat
import zipfile


def decode_text(text: str) -> bytes:
    payload = "".join(text.split())
    try:
        data = base64.b64decode(payload, validate=True)
    except (ValueError, binascii.Error) as e:
        raise ValueError("Invalid Base64 payload") from e
    if not zipfile.is_zipfile(io.BytesIO(data)):
        raise ValueError("Decoded content is not a ZIP")
    return data


def safe_extract(data: bytes, destination: Path) -> None:
    destination = destination.resolve()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for info in zf.infolist():
            path = PurePosixPath(info.filename)
            mode = info.external_attr >> 16
            if path.is_absolute() or ".." in path.parts or not path.parts:
                raise ValueError(f"Unsafe archive entry: {info.filename}")
            if stat.S_ISLNK(mode):
                raise ValueError(f"Symlinks are not supported: {info.filename}")
            target = (destination / info.filename).resolve()
            if not target.is_relative_to(destination):
                raise ValueError(f"Unsafe archive entry: {info.filename}")
        destination.mkdir(parents=True, exist_ok=True)
        zf.extractall(destination)


def main() -> None:
    ap = argparse.ArgumentParser(description="Base64 TXT → ZIP → optional directory")
    ap.add_argument("source", type=Path)
    ap.add_argument("--output", type=Path, default=Path("restored.zip"))
    ap.add_argument("--extract", type=Path)
    ap.add_argument("--sha256", help="Expected ZIP SHA-256")
    args = ap.parse_args()
    data = decode_text(args.source.read_text(encoding="ascii"))
    digest = hashlib.sha256(data).hexdigest()
    if args.sha256 and digest.lower() != args.sha256.lower():
        ap.error("SHA-256 does not match")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    if args.extract:
        safe_extract(data, args.extract)
    print(f"ZIP: {args.output} ({len(data)} bytes); SHA-256: {digest}")
    if args.extract:
        print(f"Extracted to {args.extract}")


if __name__ == "__main__":
    main()
