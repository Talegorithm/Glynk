"""
Media HTML builder — 把 ASR sentences 转成带 span_id + 时间戳的 HTML。

输出符合 video-ingestion.md 的"HTML 输出契约"：
- <meta name="media-src"> / <meta name="media-type"> 供前端检测
- 每条 sentence 一段 <p><span id data-time-start data-time-end>
- span_id 沿用 `{unit_id}-{file_idx}-p{n}-s{m}`
"""
from html import escape

from glynk.ingestion.asr import TranscriptionResult


def build_media_html(
    unit_id: str,
    title: str,
    media_filename: str,
    media_type: str,
    transcription: TranscriptionResult,
    file_idx: int = 0,
) -> str:
    """生成媒体内容的 HTML。每个 ASR sentence 一段 <p><span>。"""
    title_esc = escape(title)
    media_src = f"/media/{unit_id}/{media_filename}"

    paragraphs = []
    for i, sent in enumerate(transcription.sentences, start=1):
        span_id = f"{unit_id}-{file_idx}-p{i}-s1"
        start_s = f"{sent.begin_ms / 1000:.3f}"
        end_s = f"{sent.end_ms / 1000:.3f}"
        text_esc = escape(sent.text)
        paragraphs.append(
            f'<p><span id="{span_id}" '
            f'data-time-start="{start_s}" data-time-end="{end_s}">'
            f'{text_esc}</span></p>'
        )

    body = "\n  ".join(paragraphs)

    return (
        '<!DOCTYPE html>\n'
        '<html>\n'
        '<head>\n'
        '  <meta charset="UTF-8">\n'
        f'  <meta name="media-src" content="{escape(media_src)}">\n'
        f'  <meta name="media-type" content="{escape(media_type)}">\n'
        f'  <title>{title_esc}</title>\n'
        '</head>\n'
        '<body>\n'
        f'  <h1>{title_esc}</h1>\n'
        f'  {body}\n'
        '</body>\n'
        '</html>'
    )
