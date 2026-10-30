"""Knight Online DXT to PNG converter. Author: Zorlanis."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import struct
import sys
import time
from dataclasses import asdict, dataclass
from typing import Callable

from PIL import Image, UnidentifiedImageError

__version__ = "0.1.0"
MAX_DIMENSION = 8192
DEFAULT_SOURCE = Path(r"C:\NTTGame\KnightOnlineEn")
CIPHER = b"owsd9012%$1as!wpow1033b%!@%12"
FORMATS = {0x31545844: "dxt1", 0x32545844: "dxt2", 0x33545844: "dxt3",
           0x34545844: "dxt4", 0x35545844: "dxt5",
           21: "a8r8g8b8", 22: "x8r8g8b8", 25: "a1r5g5b5", 26: "a4r4g4b4"}
BLOCK_SIZES = {"dxt1": 8, "dxt2": 16, "dxt3": 16, "dxt4": 16, "dxt5": 16}
PREMULTIPLIED = {"dxt2": 0x33545844, "dxt4": 0x35545844}


class TextureError(ValueError):
    """Invalid, unsupported, or truncated texture data."""


@dataclass(frozen=True)
class Texture:
    name: str
    format: str
    width: int
    height: int
    pixels: bytes

    def metadata(self) -> dict:
        return {key: getattr(self, key) for key in ("name", "format", "width", "height")}

    def _image(self) -> Image.Image:
        _dimensions(self.width, self.height)
        if len(self.pixels) != self.width * self.height * 4:
            raise TextureError("RGBA buffer size does not match dimensions")
        return Image.frombytes("RGBA", (self.width, self.height), self.pixels)

    def to_png(self) -> bytes:
        output = io.BytesIO()
        with self._image() as image:
            image.save(output, format="PNG")
        return output.getvalue()

    def save_png(self, output: Path | str) -> None:
        """Create a PNG exclusively; never overwrite an existing file."""
        output = Path(output)
        with self._image() as image:
            stream = output.open("xb")
            try:
                with stream:
                    image.save(stream, format="PNG")
            except BaseException:
                # Includes Ctrl+C: do not leave a partial PNG to be skipped later.
                output.unlink(missing_ok=True)
                raise


def _dimensions(width: int, height: int) -> None:
    if not (1 <= width <= MAX_DIMENSION and 1 <= height <= MAX_DIMENSION):
        raise TextureError(f"dimensions must be 1..{MAX_DIMENSION}; got {width}x{height}")


def _rc4(key: bytes, data: bytes) -> bytes:
    state = list(range(256))
    j = 0
    for i in range(256):
        j = (j + state[i] + key[i % len(key)]) & 255
        state[i], state[j] = state[j], state[i]
    result = bytearray(len(data))
    i = j = 0
    for offset, byte in enumerate(data):
        i = (i + 1) & 255
        j = (j + state[i]) & 255
        state[i], state[j] = state[j], state[i]
        result[offset] = byte ^ state[(state[i] + state[j]) & 255]
    return bytes(result)


def _decrypt(payload: bytes, format_name: str, width: int) -> bytes:
    key = hashlib.sha1(CIPHER, usedforsecurity=False).digest()[:16]
    if format_name in BLOCK_SIZES:
        return _rc4(key, payload)
    stride = width * (2 if format_name in {"a1r5g5b5", "a4r4g4b4"} else 4)
    # The game resets RC4 for every uncompressed scanline.
    return b"".join(_rc4(key, payload[offset:offset + stride])
                    for offset in range(0, len(payload), stride))


def _straight_alpha(pixels: bytes) -> bytes:
    """Convert DXT2/4 premultiplied RGB to the straight alpha PNG expects."""
    rgba = bytearray(pixels)
    for offset in range(0, len(rgba), 4):
        alpha = rgba[offset + 3]
        if alpha == 0:
            rgba[offset:offset + 3] = b"\0\0\0"
        elif alpha < 255:
            for channel in range(offset, offset + 3):
                rgba[channel] = min(255, (rgba[channel] * 255 + alpha // 2) // alpha)
    return bytes(rgba)


def _decode_pixels(payload: bytes, width: int, height: int, code: int, name: str) -> bytes:
    if name in BLOCK_SIZES:
        # Wrap the validated top mip level in a standard DDS header so Pillow's
        # native S3TC decoder handles BC1/2/3, including partial edge blocks.
        # DXT2 has DXT3's block layout; DXT4 has DXT5's. Only DXT2/4 need
        # unpremultiplication after decoding. Metadata keeps the original name.
        decoder_code = PREMULTIPLIED.get(name, code)
        header = ([124, 0x81007, height, width, len(payload), 0, 0] + [0] * 11
                  + [32, 4, decoder_code, 0, 0, 0, 0, 0] + [0x1000, 0, 0, 0, 0])
        dds = b"DDS " + struct.pack("<31I", *header) + payload
        with Image.open(io.BytesIO(dds), formats=["DDS"]) as image:
            pixels = image.convert("RGBA").tobytes()
        return _straight_alpha(pixels) if name in PREMULTIPLIED else pixels
    if name in {"a8r8g8b8", "x8r8g8b8"}:
        mode, raw_mode = ("RGBA", "BGRA") if name == "a8r8g8b8" else ("RGB", "BGRX")
        with Image.frombytes(mode, (width, height), payload, "raw", raw_mode) as image:
            return image.convert("RGBA").tobytes()
    rgba = bytearray(width * height * 4)
    for i, (value,) in enumerate(struct.iter_unpack("<H", payload)):
        if name == "a1r5g5b5":
            pixel = (((value >> 10) & 31) * 255 // 31,
                     ((value >> 5) & 31) * 255 // 31,
                     (value & 31) * 255 // 31, 255 if value & 0x8000 else 0)
        else:
            pixel = (((value >> 8) & 15) * 17, ((value >> 4) & 15) * 17,
                     (value & 15) * 17, ((value >> 12) & 15) * 17)
        rgba[i * 4:i * 4 + 4] = bytes(pixel)
    return bytes(rgba)


def decode_texture(data: bytes) -> Texture:
    """Decode NTF or TGA 2.0 to RGBA pixels without modifying the input."""
    try:
        if data.endswith(b"TRUEVISION-XFILE.\0"):
            with Image.open(io.BytesIO(data), formats=["TGA"]) as image:
                _dimensions(*image.size)
                return Texture("", "tga", *image.size, image.convert("RGBA").tobytes())
        if len(data) < 4:
            raise TextureError("truncated header")
        name_length = struct.unpack_from("<I", data)[0]
        if name_length > 200:
            raise TextureError("name length exceeds 200 bytes")
        offset = 4 + name_length
        if len(data) < offset + 20:
            raise TextureError("truncated header")
        magic, version, width, height, code, _flags = struct.unpack_from("<3sB4I", data, offset)
        if magic != b"NTF":
            raise TextureError("missing NTF signature")
        _dimensions(width, height)
        if code not in FORMATS:
            raise TextureError(f"unsupported texture format: 0x{code:08x}")
        format_name = FORMATS[code]
        if format_name in BLOCK_SIZES:
            size = ((width + 3) // 4) * ((height + 3) // 4) * BLOCK_SIZES[format_name]
        else:
            size = width * height * (2 if code in {25, 26} else 4)
        payload = data[offset + 20:offset + 20 + size]
        if len(payload) != size:
            raise TextureError(f"truncated pixel data; need {size} bytes")
        if version == 7:
            payload = _decrypt(payload, format_name, width)
        return Texture(data[4:offset].decode("utf-8", errors="replace"), format_name,
                       width, height, _decode_pixels(payload, width, height, code, format_name))
    except (UnidentifiedImageError, OSError, struct.error) as error:
        raise TextureError(str(error)) from error


def convert_file(source: Path | str, output: Path | str) -> dict:
    source, output = Path(source), Path(output)
    texture = decode_texture(source.read_bytes())
    texture.save_png(output)
    return {"file": str(source), **texture.metadata(), "output": str(output)}


@dataclass
class Summary:
    total: int = 0
    converted: int = 0
    skipped: int = 0
    failed: int = 0


def _collect(source: Path, output: Path, report: Callable[[dict], None]) -> list[Path]:
    pending, files = [source], []
    while pending:
        folder = pending.pop()
        report({"event": "scanning", "directory": str(folder)})
        with os.scandir(folder) as entries:
            for entry in entries:
                path = Path(entry.path)
                if entry.is_symlink() or path == output:
                    continue
                if os.name == "nt" and getattr(entry.stat(follow_symlinks=False),
                                               "st_file_attributes", 0) & 0x400:
                    continue  # Windows junctions/reparse points can form cycles.
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                elif entry.is_file(follow_symlinks=False) and path.suffix.lower() == ".dxt":
                    files.append(path)
    return sorted(files)


def convert_directory(source: Path | str, output: Path | str | None = None,
                      report: Callable[[dict], None] = lambda event: None) -> Summary:
    source = Path(source).resolve(strict=True)
    if not source.is_dir():
        raise NotADirectoryError(f"input must be a folder: {source}")
    output = Path(output).resolve() if output is not None else source / "outputs"
    if source == output:
        raise ValueError("output folder must be different from the input folder")
    output.mkdir(parents=True, exist_ok=True)
    output = output.resolve()
    if source == output:
        raise ValueError("output folder must be different from the input folder")
    files = _collect(source, output, report)
    summary = Summary(total=len(files))
    report({"event": "found", "total": summary.total, "output": str(output)})
    for index, path in enumerate(files, 1):
        relative = path.relative_to(source)
        destination = (output / relative).with_suffix(".png")
        event = {"event": "file", "file": str(path), "relative": str(relative),
                 "output": str(destination), "index": index, "total": summary.total}
        try:
            if destination.exists() or destination.is_symlink():
                summary.skipped += 1
                event["status"] = "skipped"
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                event.update(convert_file(path, destination))
                summary.converted += 1
                event["status"] = "converted"
        except (OSError, ValueError) as error:
            summary.failed += 1
            event.update(status="failed", error=str(error))
        report(event)
    report({"event": "summary", **asdict(summary)})
    return summary


def _color_available() -> bool:
    if not sys.stdout.isatty() or "NO_COLOR" in os.environ or os.getenv("TERM") == "dumb":
        return False
    if os.name != "nt":
        return True
    # Enable ANSI colors in Windows consoles without another dependency.
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetStdHandle.argtypes = [wintypes.DWORD]
    kernel.GetStdHandle.restype = wintypes.HANDLE
    kernel.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    handle = kernel.GetStdHandle(-11 & 0xffffffff)
    mode = wintypes.DWORD()
    return bool(kernel.GetConsoleMode(handle, ctypes.byref(mode))
                and kernel.SetConsoleMode(handle, mode.value | 4))


class TerminalReporter:
    """Small dependency-free progress UI, or versioned NDJSON for automation."""

    def __init__(self, json_mode: bool = False, no_color: bool = False):
        self.json_mode = json_mode
        self.tty = not json_mode and sys.stdout.isatty()
        self.color = not json_mode and not no_color and _color_available()
        self.stats = Summary()
        self.started = time.monotonic()
        self.active_width = 0

    def style(self, text: str, code: str = "36") -> str:
        return f"\033[{code}m{text}\033[0m" if self.color else text

    @staticmethod
    def safe(text: str) -> str:
        return text.replace("\x1b", "?").replace("\r", " ").replace("\n", " ")

    def clear(self) -> None:
        if self.active_width:
            sys.stdout.write("\r" + " " * self.active_width + "\r")
            sys.stdout.flush()
            self.active_width = 0

    def close(self) -> None:
        if self.active_width:
            print(flush=True)
            self.active_width = 0

    def paint(self, plain: str, styled: str | None = None) -> None:
        if self.tty:
            sys.stdout.write("\r" + (styled or plain) + " " * max(0, self.active_width - len(plain)))
            sys.stdout.flush()
            self.active_width = len(plain)
        else:
            print(plain, flush=True)

    def snapshot(self) -> dict:
        done = self.stats.converted + self.stats.skipped + self.stats.failed
        return {**asdict(self.stats), "processed": done,
                "remaining": max(0, self.stats.total - done),
                "percent": round(done * 100 / self.stats.total, 1) if self.stats.total else 0.0}

    def progress(self) -> None:
        stats = self.snapshot()
        if not stats["total"]:
            return
        tail = (f" {int(stats['percent']):3d}%  Yapılan:{stats['converted']}"
                f"  Kalan:{stats['remaining']}  Atlanan:{stats['skipped']}  Hata:{stats['failed']}")
        columns = shutil.get_terminal_size((90, 24)).columns
        width = max(6, min(26, columns - len(tail) - 6))
        filled = stats["processed"] * width // stats["total"]
        bar = "█" * filled + "░" * (width - filled)
        plain = f"  [{bar}]{tail}"
        styled = f"  [{self.style(bar)}]{tail}"
        self.paint(plain, styled)

    def report(self, event: dict) -> None:
        kind = event["event"]
        if kind == "found":
            self.stats = Summary(total=event["total"])
            self.started = time.monotonic()
        elif kind == "file":
            self.stats.total = event["total"]
            field = {"converted": "converted", "skipped": "skipped", "failed": "failed"}[event["status"]]
            setattr(self.stats, field, getattr(self.stats, field) + 1)
        elif kind == "summary":
            self.stats = Summary(**{field: event[field] for field in ("total", "converted", "skipped", "failed")})
        if self.json_mode:
            print(json.dumps({"schema_version": 1, **event, **self.snapshot()}, ensure_ascii=False), flush=True)
            return
        if kind == "scanning":
            path = self.safe(event["directory"])
            if self.tty:
                width = max(20, shutil.get_terminal_size((90, 24)).columns - 18)
                if len(path) > width:
                    path = "…" + path[-width + 1:]
                line = f"  Taranıyor · {path}"
                self.paint(line, self.style(line, "90"))
            else:
                print(f"TARA  {path}", flush=True)
        elif kind == "found":
            self.clear()
            print(self.style(f"\n  {event['total']} DXT dosyası bulundu.", "36;1"))
            print(f"  Çıktı: {self.safe(event['output'])}")
            if event["total"]:
                print("  Dönüştürme otomatik başlıyor…\n", flush=True)
                self.progress()
            else:
                print("  Bu klasörde dönüştürülecek DXT dosyası yok.")
        elif kind == "file":
            if event["status"] == "failed":
                self.clear()
                print(self.style(f"  HATA · {self.safe(event['file'])}: {self.safe(event['error'])}", "31"),
                      file=sys.stderr, flush=True)
            self.progress()
        elif kind == "summary":
            self.close()
            elapsed = time.monotonic() - self.started
            title = "HATALARLA TAMAMLANDI" if self.stats.failed else "TAMAMLANDI"
            print(self.style(f"\n  {title}", "33;1" if self.stats.failed else "32;1"))
            print(f"  {self.stats.converted} PNG oluşturuldu · {self.stats.skipped} atlandı"
                  f" · {self.stats.failed} hata · {elapsed:.1f} sn\n", flush=True)
        elif kind in {"error", "cancelled"}:
            self.clear()
            message = event.get("error", event.get("message", "İşlem durduruldu."))
            print(self.style(f"\n  {self.safe(message)}", "31" if kind == "error" else "33"),
                  file=sys.stderr, flush=True)


def _prompt_source(console: TerminalReporter) -> Path:
    print(console.style(f"\n  DXT → PNG  v{__version__}", "36;1"))
    print("  Zorlanis · Knight Online doku dönüştürücü")
    print(console.style("  " + "─" * 48, "90"))
    print(f"\n  Varsayılan: {DEFAULT_SOURCE}")
    print("  Enter: varsayılan klasör · Ctrl+C: çıkış\n")
    while True:
        value = input("  DXT klasörü > ").strip().strip('"\'')
        source = Path(os.path.expandvars(value)).expanduser() if value else DEFAULT_SOURCE
        if source.is_dir():
            return source
        print(console.style(f"  Klasör bulunamadı: {console.safe(str(source))}", "31"))
        print("  Geçerli bir klasör yolu girip yeniden dene.\n")


def main(argv: list[str] | None = None) -> int:
    # Keep redirected output and installed console scripts UTF-8 on Windows too.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="dxt2png", description="Knight Online DXT → PNG | Zorlanis",
                                     epilog="Sihirbaz: dxt2png | Otomasyon: dxt2png -d textures --json")
    parser.add_argument("input", nargs="?", type=Path, help="DXT dosyası veya kaynak klasör")
    parser.add_argument("-d", "--directory", nargs="?", const=DEFAULT_SOURCE, type=Path, metavar="DIR",
                        help=f"alt klasörlerle toplu dönüştür; varsayılan: {DEFAULT_SOURCE}")
    parser.add_argument("-o", "--output", type=Path, metavar="PATH", help="çıktı dosyası veya toplu çıktı klasörü")
    parser.add_argument("--json", action="store_true", help="her olayı ayrı bir JSON satırı olarak yaz")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("-i", "--interactive", action="store_true", help="klasör soran terminal sihirbazını aç")
    modes.add_argument("--non-interactive", action="store_true", help="soru sorma; klasör verilmezse varsayılanı kullan")
    parser.add_argument("--no-color", action="store_true", help="terminal renklerini kapat")
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__} · Zorlanis")
    args = parser.parse_args(argv)
    if args.input is not None and args.directory is not None:
        parser.error("input ve --directory birlikte kullanılamaz")
    if args.json and args.interactive:
        parser.error("--json ve --interactive birlikte kullanılamaz")
    source = args.directory if args.directory is not None else args.input
    directory_mode = args.directory is not None
    console = TerminalReporter(args.json, args.no_color)
    try:
        if source is None:
            unattended = args.json or args.non_interactive or (not args.interactive and not sys.stdin.isatty())
            source = DEFAULT_SOURCE if unattended else _prompt_source(console)
            directory_mode = True
        if directory_mode or source.is_dir():
            result = convert_directory(source, args.output, console.report)
            return 1 if result.failed else 0
        output = args.output if args.output is not None else source.with_suffix(".png")
        result = convert_file(source, output)
        console.report({"event": "file", "status": "converted", "index": 1, "total": 1, **result})
        return 0
    except KeyboardInterrupt:
        console.report({"event": "cancelled", "message": "Durduruldu. Tamamlanan PNG dosyaları korundu."})
        return 130
    except EOFError:
        console.report({"event": "error", "error": "Klasör girişi alınamadı. Otomasyon için --non-interactive veya --json kullan."})
        return 2
    except (OSError, ValueError) as error:
        console.report({"event": "error", "error": str(error)})
        return 1
    finally:
        console.close()


if __name__ == "__main__":
    raise SystemExit(main())
