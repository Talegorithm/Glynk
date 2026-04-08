"""
迁移脚本：将已有内容的 TOC href 从 EPUB 原始格式转换为 span_id

运行方式：
  cd /path/to/Glynk && python scripts/migrate_toc.py
"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from bs4 import BeautifulSoup
from glynk.storage.postgres import PostgresStore
from glynk.config import StorageConfig

def get_file_first_span(html_root: Path, content_id: str, file_idx: int) -> str:
    file_path = html_root / content_id / f"{file_idx}.html"
    if not file_path.exists():
        return ""
    html = file_path.read_text(encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    first = soup.find('span', id=True)
    return first.get('id') if first else ""


def migrate_content_toc(db: PostgresStore, html_root: Path, content_id: str):
    content = db.get_content(content_id)
    if not content:
        print(f"  Content {content_id} not found")
        return

    toc = json.loads(content.get('toc_json', '[]'))
    if not toc:
        print(f"  Content {content_id}: no TOC")
        return

    file_count = content.get('file_count', 0)

    # Build file_first_span mapping
    file_first_span = {}
    for idx in range(file_count):
        span = get_file_first_span(html_root, content_id, idx)
        if span:
            file_first_span[idx] = span

    # Check if already migrated (first toc item has span_id format)
    first_href = toc[0].get('href', '')
    if first_href and '-p' in first_href and '-s' in first_href:
        print(f"  Content {content_id}: already migrated")
        return

    # Simple approach: map each TOC item to the nearest file's first span
    # by matching the file index from the href order
    mapped = 0
    failed = 0

    # For EPUBs, the TOC hrefs are in reading order, so we can map
    # them by the file index they correspond to
    def process_items(items, depth=1):
        nonlocal mapped, failed
        for item in items:
            item['level'] = depth
            href = item.get('href', '')

            if href:
                # Try to find which file_idx this href corresponds to
                # Strategy: iterate through files and check if the href matches
                found = False
                for idx in range(file_count):
                    html_file = html_root / content_id / f"{idx}.html"
                    if not html_file.exists():
                        continue

                    # Check if this file was generated from the EPUB file mentioned in href
                    # Simple heuristic: check if any heading in this file matches the TOC title
                    if not found:
                        html = html_file.read_text(encoding='utf-8')
                        soup = BeautifulSoup(html, 'html.parser')

                        # Check headings for title match
                        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
                            heading_text = heading.get_text(strip=True)
                            if heading_text and item['title'] and heading_text == item['title']:
                                # Found match! Get the first span in this heading or after it
                                span = heading.find('span', id=True)
                                if not span:
                                    span = heading.find_next('span', id=True)
                                if span and span.get('id'):
                                    item['href'] = span.get('id')
                                    mapped += 1
                                    found = True
                                    break

                if not found:
                    # Fallback: leave href empty
                    item['href'] = ''
                    failed += 1

            if item.get('children'):
                process_items(item['children'], depth + 1)

    process_items(toc)

    # Save updated TOC
    db._execute(
        "UPDATE contents SET toc_json = %s WHERE content_id = %s",
        (json.dumps(toc, ensure_ascii=False), content_id)
    )

    print(f"  Content {content_id}: mapped={mapped}, failed={failed}, total={mapped+failed}")


def main():
    config = StorageConfig(
        postgres_host=os.getenv('POSTGRES_HOST', 'localhost'),
        postgres_port=int(os.getenv('POSTGRES_PORT', '5432')),
        postgres_user=os.getenv('POSTGRES_USER', 'glynk'),
        postgres_password=os.getenv('POSTGRES_PASSWORD', 'glynk'),
        postgres_db=os.getenv('POSTGRES_DB', 'glynk'),
    )
    db = PostgresStore(config)

    html_root = Path(os.getenv('DATA_ROOT', '/tmp/glynk-data')) / 'html'

    contents = db.list_contents(limit=500)
    print(f"Found {len(contents)} contents to migrate")

    for c in contents:
        print(f"\nProcessing: {c['title'][:40]} ({c['content_id']})")
        migrate_content_toc(db, html_root, c['content_id'])

    print("\nDone!")


if __name__ == '__main__':
    main()
