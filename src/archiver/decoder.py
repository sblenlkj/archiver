"""Decode ZIP/Base64 from one TXT or numbered local TXT split files."""
import argparse
import base64
import binascii
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile

MANIFEST = "manifest.json"


def decode_text(text: str) -> bytes:
    payload = "".join(text.split())
    try:
        data = base64.b64decode(payload, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Invalid Base64 payload") from exc
    if not zipfile.is_zipfile(io.BytesIO(data)):
        raise ValueError("Decoded content is not a ZIP")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise ValueError(f"ZIP CRC check failed for {bad}")
    return data


def read_splits(folder: Path) -> tuple[str, str | None]:
    if not folder.is_dir():
        raise ValueError(f"Split directory not found: {folder}")
    manifest_path = folder / MANIFEST
    if not manifest_path.is_file():
        raise ValueError(f"Missing {MANIFEST}; cannot verify that all parts are present")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format") != "archiver-splits-v1":
        raise ValueError("Unsupported split manifest format")
    count = manifest.get("parts")
    if type(count) is not int or count < 1:
        raise ValueError("Invalid parts count in manifest")

    numbered = {}
    for file in folder.iterdir():
        if file.name == MANIFEST:
            continue
        if file.is_symlink() or not file.is_file() or file.suffix != ".txt" or not file.stem.isdecimal():
            raise ValueError(f"Unexpected entry in splits directory: {file.name}")
        index = int(file.stem)
        if index in numbered:
            raise ValueError(f"Duplicate part number: {index}")
        numbered[index] = file

    expected = set(range(1, count + 1))
    missing = sorted(expected - numbered.keys())
    extra = sorted(numbered.keys() - expected)
    if missing or extra:
        raise ValueError(f"Split parts mismatch: missing={missing}, extra={extra}")

    chunks = [numbered[index].read_text(encoding="ascii") for index in range(1, count + 1)]
    payload = "".join(chunks)
    if len(payload) != manifest.get("characters"):
        raise ValueError("Reassembled Base64 length mismatch")
    actual_hash = hashlib.sha256(payload.encode("ascii")).hexdigest()
    if actual_hash != manifest.get("base64_sha256"):
        raise ValueError("Reassembled Base64 SHA-256 mismatch")
    return payload, manifest.get("zip_sha256")


def safe_extract(data: bytes, destination: Path) -> None:
    destination = destination.resolve()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for info in archive.infolist():
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
        archive.extractall(destination)


def main() -> None:
    ap = argparse.ArgumentParser(description="Base64 TXT or splits → ZIP → optional directory")
    ap.add_argument("source", nargs="?", type=Path, help="Single Base64 TXT file")
    ap.add_argument("--splits", nargs="?", type=Path, const=Path("decoded/splits"),
                    metavar="DIR", help="Read numbered TXT files from DIR (default: decoded/splits/)")
    ap.add_argument("--output", type=Path, default=Path("decoded/restored.zip"))
    ap.add_argument("--extract", type=Path)
    ap.add_argument("--sha256", help="Expected ZIP SHA-256")
    args = ap.parse_args()
    if (args.source is None) == (args.splits is None):
        ap.error("Specify exactly one of SOURCE or --splits [DIR]")

    try:
        if args.splits is not None:
            encoded, manifest_hash = read_splits(args.splits)
            print(f"Assembled Base64 from {args.splits} ({len(encoded)} characters)")
        else:
            encoded = args.source.read_text(encoding="ascii")
            manifest_hash = None
        data = decode_text(encoded)
        digest = hashlib.sha256(data).hexdigest()
        if manifest_hash and digest != manifest_hash:
            raise ValueError("ZIP SHA-256 differs from split manifest")
        if args.sha256 and digest.lower() != args.sha256.lower():
            raise ValueError("ZIP SHA-256 does not match --sha256")
        if args.extract:
            safe_extract(data, args.extract)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(data)
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        ap.error(str(exc))

    print(f"ZIP: {args.output} ({len(data)} bytes); SHA-256: {digest}")
    if args.extract:
        print(f"Extracted to {args.extract}")


if __name__ == "__main__":
    main()
