"""
Qwen3-ASR 转写。后端"结构化处理"的例外口子（见 requirements.md §3.6）。

用 `dashscope.audio.qwen_asr.QwenTranscription`（注意 file_url 单数，不是通用
Transcription 的 file_urls 列表），返回句+字级时间戳。
"""
import json
import logging
import time
import urllib.request
from dataclasses import dataclass, field

from dashscope.audio.qwen_asr.qwen_transcription import QwenTranscription

from glynk.config import ASRConfig

logger = logging.getLogger(__name__)

_POLL_INTERVAL_SECONDS = 3
_MAX_POLL_SECONDS = 30 * 60  # 30 min 上限；长音频也够了


@dataclass
class Word:
    text: str
    begin_ms: int
    end_ms: int
    punctuation: str = ""


@dataclass
class Sentence:
    sentence_id: int
    text: str
    begin_ms: int
    end_ms: int
    language: str = ""
    emotion: str = ""
    words: list[Word] = field(default_factory=list)


@dataclass
class TranscriptionResult:
    sentences: list[Sentence]
    duration_ms: int
    sample_rate: int
    audio_format: str
    raw: dict  # 原始 JSON，归档用


def transcribe(file_url: str, config: ASRConfig) -> TranscriptionResult:
    """提交转写任务，阻塞至完成，返回结构化结果。"""
    if not config.api_key:
        raise RuntimeError("ALI_API_KEY not configured (DashScope API key, sk-... format)")

    task = QwenTranscription.async_call(
        model=config.model,
        file_url=file_url,
        api_key=config.api_key,
        enable_words=True,
        language_hints=list(config.language_hints),
    )
    if task.status_code != 200:
        raise RuntimeError(f"ASR submit failed: {task.status_code} {task.message}")

    task_id = task.output["task_id"]
    logger.info(f"ASR task submitted: {task_id}")

    elapsed = 0
    while elapsed < _MAX_POLL_SECONDS:
        time.sleep(_POLL_INTERVAL_SECONDS)
        elapsed += _POLL_INTERVAL_SECONDS
        r = QwenTranscription.fetch(task=task_id, api_key=config.api_key)
        status = r.output.get("task_status")
        if status == "SUCCEEDED":
            break
        if status == "FAILED":
            raise RuntimeError(f"ASR task failed: {r.output}")
    else:
        raise TimeoutError(f"ASR task {task_id} did not finish within {_MAX_POLL_SECONDS}s")

    result_url = r.output["result"]["transcription_url"]
    logger.info(f"ASR task {task_id} succeeded in {elapsed}s")

    with urllib.request.urlopen(result_url, timeout=60) as f:
        data = json.loads(f.read())

    return _parse_result(data)


def _parse_result(data: dict) -> TranscriptionResult:
    audio_info = data.get("audio_info", {})
    transcripts = data.get("transcripts", [])
    if not transcripts:
        raise RuntimeError("ASR returned no transcripts")

    t = transcripts[0]
    sentences = []
    for s in t.get("sentences", []):
        sentences.append(Sentence(
            sentence_id=s.get("sentence_id", 0),
            text=s.get("text", ""),
            begin_ms=s.get("begin_time", 0),
            end_ms=s.get("end_time", 0),
            language=s.get("language", ""),
            emotion=s.get("emotion", ""),
            words=[Word(
                text=w.get("text", ""),
                begin_ms=w.get("begin_time", 0),
                end_ms=w.get("end_time", 0),
                punctuation=w.get("punctuation", ""),
            ) for w in s.get("words", [])],
        ))

    duration_ms = 0
    if sentences:
        duration_ms = sentences[-1].end_ms
    # 优先用 audio_info 的 duration（如果提供）
    duration_ms = audio_info.get("duration", duration_ms) or duration_ms

    return TranscriptionResult(
        sentences=sentences,
        duration_ms=duration_ms,
        sample_rate=audio_info.get("sample_rate", 0),
        audio_format=audio_info.get("format", ""),
        raw=data,
    )
