"""
Anchor 迁移 —— 在 Publication 内容更新时，把 span 级 anchor 从旧内容重新定位到新内容。

Unit 身份不变（unit_id 稳定）；只需要在**同一个 Unit 内**做 span 重映射。

Tier 1: 旧 span 文本在新内容中唯一精确匹配 → 更新 target_span
Tier 2: 模糊匹配 >= 85% → 更新 target_span，标 confidence=fuzzy
Tier 3: 找不到 → target_span=null（降级为 Unit 级），保留原文供 Agent 后续重定位
"""
import logging
from difflib import SequenceMatcher

from bs4 import BeautifulSoup
from psycopg2.extras import Json

logger = logging.getLogger(__name__)

FUZZY_THRESHOLD = 0.85


def _extract_span_texts(html: str) -> dict[str, str]:
    """从一份 HTML 里抽所有 <span id="...">text</span>。返回 span_id → text。"""
    soup = BeautifulSoup(html, 'html.parser')
    return {
        s['id']: s.get_text(strip=True)
        for s in soup.find_all('span', id=True)
    }


def _find_fuzzy_match(old_text: str, candidates: list[tuple[str, str]],
                      threshold: float = FUZZY_THRESHOLD) -> tuple[str, float] | None:
    """在候选 (span_id, text) 中找与 old_text 相似度最高的。超过阈值才返回。"""
    best: tuple[str, float] | None = None
    for span_id, text in candidates:
        if not text:
            continue
        score = SequenceMatcher(None, old_text, text).ratio()
        if best is None or score > best[1]:
            best = (span_id, score)
    if best and best[1] >= threshold:
        return best
    return None


def migrate_span_anchors(unit_id: str, db, old_htmls: dict[int, str],
                         new_htmls: dict[int, str]) -> dict[str, int]:
    """
    把 target_unit=unit_id 且 target_span 非空的 anchor 从旧 span 迁到新 span。

    Args:
        unit_id: 被更新的 Unit
        db: PostgresStore
        old_htmls: {file_idx: old_html_content}
        new_htmls: {file_idx: new_html_content}

    Returns:
        {'exact': N, 'fuzzy': N, 'orphan': N, 'unchanged': N}
    """
    # 1. 抽旧 HTML 的所有 span 文本
    old_spans: dict[str, str] = {}
    for html in old_htmls.values():
        old_spans.update(_extract_span_texts(html))

    # 2. 抽新 HTML 的所有 span 文本 + 建 text → span_ids 索引
    new_spans_list: list[tuple[str, str]] = []
    text_to_spans: dict[str, list[str]] = {}
    for html in new_htmls.values():
        for span_id, text in _extract_span_texts(html).items():
            new_spans_list.append((span_id, text))
            text_to_spans.setdefault(text, []).append(span_id)

    # 3. 取出所有受影响的 anchor
    anchors = db.execute_query(
        """SELECT id, target_span, metadata
           FROM anchors
           WHERE target_unit = %s AND target_span IS NOT NULL""",
        (unit_id,),
    )

    stats = {'exact': 0, 'fuzzy': 0, 'orphan': 0, 'unchanged': 0}

    for anchor in anchors:
        old_span_id = anchor['target_span']
        old_text = old_spans.get(old_span_id, "")

        if not old_text:
            # 旧 HTML 里找不到这个 span 的文本，降级为 orphan
            _set_orphan(db, anchor, old_span_id, "")
            stats['orphan'] += 1
            continue

        # Tier 1: 新内容中文本未变且唯一 → 新 span_id 可能不同（因为位置变了）
        matches = text_to_spans.get(old_text, [])
        if len(matches) == 1:
            new_span_id = matches[0]
            if new_span_id == old_span_id:
                stats['unchanged'] += 1
            else:
                _set_span(db, anchor, new_span_id, confidence='exact')
                stats['exact'] += 1
            continue

        if len(matches) > 1:
            # 多处同样文本，尝试保持位置最接近的
            # 简化：选 file_idx 最小的那个（靠前的）
            new_span_id = sorted(matches)[0]
            _set_span(db, anchor, new_span_id, confidence='exact_ambiguous')
            stats['exact'] += 1
            continue

        # Tier 2: 模糊匹配
        fuzzy = _find_fuzzy_match(old_text, new_spans_list)
        if fuzzy:
            new_span_id, similarity = fuzzy
            _set_span(db, anchor, new_span_id, confidence='fuzzy',
                      similarity=round(similarity, 3))
            stats['fuzzy'] += 1
            continue

        # Tier 3: 降级为 Unit 级
        _set_orphan(db, anchor, old_span_id, old_text)
        stats['orphan'] += 1

    logger.info(f"Anchor migration for {unit_id}: {stats}")
    return stats


def _set_span(db, anchor: dict, new_span_id: str, confidence: str,
              similarity: float | None = None) -> None:
    """把 anchor 指向新 span，metadata 记录迁移信息。"""
    metadata = dict(anchor.get('metadata') or {})
    migration = {
        'confidence': confidence,
        'old_span': anchor['target_span'],
    }
    if similarity is not None:
        migration['similarity'] = similarity
    metadata['migration'] = migration
    db._execute(
        "UPDATE anchors SET target_span = %s, metadata = %s WHERE id = %s",
        (new_span_id, Json(metadata), anchor['id']),
    )


def _set_orphan(db, anchor: dict, old_span_id: str, old_text: str) -> None:
    """降级为 Unit 级 anchor：target_span=null，保留 original_text 供后续人工/agent 重定位。"""
    metadata = dict(anchor.get('metadata') or {})
    metadata['migration'] = {
        'confidence': 'orphan',
        'old_span': old_span_id,
        'original_text': old_text,
    }
    # target_type 同时要从 span 降为 unit
    db._execute(
        """UPDATE anchors SET target_span = NULL, target_type = 'unit',
                              metadata = %s WHERE id = %s""",
        (Json(metadata), anchor['id']),
    )
