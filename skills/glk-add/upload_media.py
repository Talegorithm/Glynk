#!/usr/bin/env python3
"""
媒体上传工具（自包含，零外部依赖）

音频/视频 → Glynk。后端异步转写 + 时间戳对齐，产出可阅读 + 可播放 + 可标注的 Unit。

流程：
  1. 本地 ffmpeg：非 mp3/wav/mp4 容器 → 先转 mp3（DashScope 对容器挑食）
  2. 计算 sha256
  3. POST /api/publications/media/init     → 拿 OSS presigned PUT URL
  4. PUT 到 OSS                            → 直接上传，不过后端带宽
  5. POST /api/publications/media/finalize → 后端转写 + 建 HTML，同步返回 IngestResult

用法:
  python upload_media.py clip.m4a --title "Lex Fridman #401" --source-url https://... --author "Lex"
  python upload_media.py video.mp4 --media-type video --title "Demo"

环境变量:
  GLYNK_API_URL  服务器地址（默认 http://localhost:8000）
  GLYNK_TOKEN    认证 token
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError


AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma"}
VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".avi"}
PASSTHROUGH_EXTS = {".mp3", ".wav", ".mp4"}  # DashScope 直接收


def infer_media_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in VIDEO_EXTS:
        return "video"
    if ext in AUDIO_EXTS:
        return "audio"
    raise SystemExit(f"Can't infer media_type from extension {ext!r}; pass --media-type")


def ensure_ffmpeg_available() -> None:
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg not found in PATH; install it (brew install ffmpeg)")


def convert_to_mp3(src: Path, out_dir: Path) -> Path:
    ensure_ffmpeg_available()
    out = out_dir / (src.stem + ".mp3")
    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-vn", "-ar", "16000", "-ac", "1",
        "-c:a", "libmp3lame", "-b:a", "64k",
        str(out),
    ]
    print(f"Converting {src.name} → {out.name} ...")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out


def sha256_hex(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def post_json(url: str, token: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        raise SystemExit(f"POST {url} failed: {e.code} {e.read().decode()}")


def put_file(url: str, path: Path) -> None:
    size = path.stat().st_size
    with path.open("rb") as f:
        req = Request(url, data=f.read(), method="PUT")
        # 关键：不显式设 Content-Type，urllib 会默认填 form-urlencoded 让 OSS 签名校验失败
        req.add_header("Content-Type", "application/octet-stream")
        req.add_header("Content-Length", str(size))
        try:
            with urlopen(req, timeout=600) as resp:
                if resp.status >= 300:
                    raise SystemExit(f"PUT failed: {resp.status}")
        except HTTPError as e:
            raise SystemExit(f"PUT to OSS failed: {e.code} {e.read().decode()}")


def upload(
    file_path: Path,
    title: str,
    server: str,
    token: str,
    media_type: str | None = None,
    source_url: str | None = None,
    author: str | None = None,
    keep_converted: bool = False,
) -> dict:
    if media_type is None:
        media_type = infer_media_type(file_path)

    # 转码（m4a 等容器 DashScope 不吃）
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        if file_path.suffix.lower() in PASSTHROUGH_EXTS:
            upload_path = file_path
        else:
            upload_path = convert_to_mp3(file_path, tmp)

        file_hash = sha256_hex(upload_path)
        print(f"sha256: {file_hash[:16]}... ({upload_path.stat().st_size} bytes)")

        init_payload = {
            "filename": upload_path.name,
            "file_hash": file_hash,
            "media_type": media_type,
            "title": title,
            "source_url": source_url,
            "author": author,
        }
        init = post_json(f"{server.rstrip('/')}/api/publications/media/init", token, init_payload)

        unit_id = init["unit_id"]
        if init.get("existing"):
            print(f"Already exists: unit_id={unit_id}")
            return {"content_id": unit_id, "existing": True}

        print(f"Uploading to OSS ...")
        put_file(init["upload_url"], upload_path)

        if keep_converted and upload_path != file_path:
            dest = file_path.with_suffix(".mp3")
            shutil.copy2(upload_path, dest)
            print(f"Converted file saved: {dest}")

        print("Finalizing ...")
        finalize_payload = {
            **init_payload,
            "unit_id": unit_id,
        }
        result = post_json(
            f"{server.rstrip('/')}/api/publications/media/finalize", token, finalize_payload
        )

    if result.get("existing"):
        print(f"Already exists: unit_id={result.get('content_id')}")
    else:
        print(
            f"Success! unit_id={result.get('content_id')}, "
            f"title={result.get('title')}, {result.get('total_chars')} chars"
        )
    return result


def main():
    parser = argparse.ArgumentParser(description="Upload media (audio/video) to Glynk")
    parser.add_argument("file", type=Path, help="Media file path")
    parser.add_argument("--title", required=True)
    parser.add_argument("--media-type", choices=["audio", "video"],
                        help="inferred from extension if omitted")
    parser.add_argument("--source-url")
    parser.add_argument("--author")
    parser.add_argument("--keep-converted", action="store_true",
                        help="save the transcoded mp3 next to original")
    parser.add_argument("--server", default=os.environ.get("GLYNK_API_URL", "http://localhost:8000"))
    parser.add_argument("--token", default=os.environ.get("GLYNK_TOKEN"))

    args = parser.parse_args()

    if not args.token:
        sys.exit("Error: --token required (or set GLYNK_TOKEN)")
    if not args.file.exists():
        sys.exit(f"File not found: {args.file}")

    upload(
        file_path=args.file,
        title=args.title,
        server=args.server,
        token=args.token,
        media_type=args.media_type,
        source_url=args.source_url,
        author=args.author,
        keep_converted=args.keep_converted,
    )


if __name__ == "__main__":
    main()
