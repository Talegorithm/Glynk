#!/usr/bin/env python3
"""
Markdown 上传工具（自包含，零外部依赖）

将本地 Markdown 文件（及其引用的图片）上传到 Glynk 服务器。
自动扫描 ![](本地路径) 引用，有图片时打包成 zip 上传。

用法:
  python upload_md.py post.md --server https://brainow.link --token TOKEN
  python upload_md.py post.md  # 默认用环境变量 GLYNK_API_URL 和 GLYNK_TOKEN

环境变量:
  GLYNK_API_URL  服务器地址（默认 http://localhost:8000）
  GLYNK_TOKEN    认证 token
"""
import argparse
import io
import json
import os
import re
import sys
import uuid
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def find_local_images(md_text: str) -> list[str]:
    refs = []
    for match in re.finditer(r'!\[.*?\]\(([^)]+)\)', md_text):
        path = match.group(1).split(' ')[0]
        if not path.startswith(('http://', 'https://', '/')):
            refs.append(path)
    return refs


def multipart_encode(fields: dict, files: dict) -> tuple[bytes, str]:
    """Build multipart/form-data body using stdlib only."""
    boundary = uuid.uuid4().hex
    lines = []
    for key, value in fields.items():
        lines.append(f'--{boundary}'.encode())
        lines.append(f'Content-Disposition: form-data; name="{key}"'.encode())
        lines.append(b'')
        lines.append(value.encode() if isinstance(value, str) else value)
    for key, (filename, data, content_type) in files.items():
        lines.append(f'--{boundary}'.encode())
        lines.append(f'Content-Disposition: form-data; name="{key}"; filename="{filename}"'.encode())
        lines.append(f'Content-Type: {content_type}'.encode())
        lines.append(b'')
        lines.append(data)
    lines.append(f'--{boundary}--'.encode())
    lines.append(b'')
    body = b'\r\n'.join(lines)
    content_type = f'multipart/form-data; boundary={boundary}'
    return body, content_type


def upload(md_path: Path, server: str, token: str) -> dict:
    md_text = md_path.read_text(encoding='utf-8')
    image_refs = find_local_images(md_text)

    md_dir = md_path.parent
    local_images: dict[str, Path] = {}
    missing = []
    for ref in image_refs:
        img_path = md_dir / ref
        if img_path.exists():
            local_images[ref] = img_path
        else:
            missing.append(ref)

    if missing:
        print(f"Warning: {len(missing)} image(s) not found:")
        for m in missing:
            print(f"  - {m}")

    if local_images:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(md_path, md_path.name)
            for ref, img_path in local_images.items():
                zf.write(img_path, ref)
        buf.seek(0)
        filename = md_path.with_suffix('.zip').name
        content_type = 'application/zip'
        file_data = buf.read()
    else:
        filename = md_path.name
        content_type = 'text/markdown'
        file_data = md_text.encode('utf-8')

    url = f"{server.rstrip('/')}/api/ingest/upload"
    print(f"Uploading {filename} to {url} ...")

    body, ct = multipart_encode({}, {"file": (filename, file_data, content_type)})
    req = Request(url, data=body, method='POST')
    req.add_header('Content-Type', ct)
    req.add_header('Authorization', f'Bearer {token}')

    try:
        with urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
    except HTTPError as e:
        print(f"Error {e.code}: {e.read().decode()}")
        sys.exit(1)

    if result.get("existing"):
        print(f"Content already exists: {result.get('content_id')}")
    else:
        print(f"Success! unit_id={result.get('content_id')}, title={result.get('title')}")
        if local_images:
            print(f"  {len(local_images)} image(s) uploaded")

    return result


def main():
    parser = argparse.ArgumentParser(description="Upload Markdown to Glynk")
    parser.add_argument("file", type=Path, help="Markdown file path")
    parser.add_argument("--server", default=os.environ.get("GLYNK_API_URL", "http://localhost:8000"))
    parser.add_argument("--token", default=os.environ.get("GLYNK_TOKEN"))

    args = parser.parse_args()

    if not args.token:
        print("Error: --token required (or set GLYNK_TOKEN)")
        sys.exit(1)
    if not args.file.exists():
        print(f"File not found: {args.file}")
        sys.exit(1)
    if args.file.suffix.lower() != '.md':
        print(f"Expected .md file, got: {args.file.suffix}")
        sys.exit(1)

    upload(args.file, args.server, args.token)


if __name__ == "__main__":
    main()
