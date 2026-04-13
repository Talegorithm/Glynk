#!/usr/bin/env python3
"""
使用 Qwen3-ASR-Flash 转录音频文件。
当前中文 ASR SOTA（CER 3.76%），英文专有名词识别远优于 Whisper。

依赖：pip install qwen3-asr-toolkit

环境变量：
  DASHSCOPE_API_KEY（必须）
"""

import os
import sys
import argparse
import numpy as np
import soundfile as sf
import silero_vad
from qwen3_asr_toolkit.audio_tools import load_audio, process_vad
from qwen3_asr_toolkit.qwen3asr import QwenASR


def transcribe_file(audio_path, model="qwen3-asr-flash"):
    print(f"加载音频: {audio_path}")
    wav = load_audio(audio_path)
    duration = len(wav) / 16000
    print(f"时长: {duration:.0f}s ({duration/60:.1f}min)")

    print("VAD 分段中...")
    vad_model = silero_vad.load_silero_vad()
    segments = process_vad(wav, vad_model)
    print(f"分为 {len(segments)} 段")

    asr = QwenASR(model=model)
    all_text = []

    for i, (start, end, audio) in enumerate(segments):
        tmp_path = f"/tmp/qwen3_seg_{i}.wav"
        sf.write(tmp_path, audio, 16000)
        dur = len(audio) / 16000
        print(f"[{i+1}/{len(segments)}] {dur:.0f}s", end=" ")
        try:
            lang, text = asr.asr(tmp_path)
            if text.strip():
                all_text.append(text)
                print(f"ok ({len(text)}字)")
            else:
                print("(空)")
        except Exception as e:
            print(f"错误: {e}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    return "\n".join(all_text)


def main():
    parser = argparse.ArgumentParser(description="Qwen3-ASR 语音转录")
    parser.add_argument("files", nargs="+", help="音频文件路径")
    parser.add_argument("-o", "--output-dir", default=".", help="输出目录")
    parser.add_argument("-k", "--key", help="DashScope API Key")
    args = parser.parse_args()

    if args.key:
        os.environ["DASHSCOPE_API_KEY"] = args.key
    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("错误: 请设置 DASHSCOPE_API_KEY 环境变量或使用 -k 参数")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    for audio_file in args.files:
        name = os.path.splitext(os.path.basename(audio_file))[0]
        print(f"\n{'='*50}\n处理: {name}\n{'='*50}")

        text = transcribe_file(audio_file)

        txt_path = os.path.join(args.output_dir, f"{name}_qwen3asr.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"\n已保存: {txt_path} ({len(text)}字)")


if __name__ == "__main__":
    main()
