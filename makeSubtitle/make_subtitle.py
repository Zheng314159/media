#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_subtitle.py - 自动为视频生成字幕并烧录到视频中
依赖:
    pip install faster-whisper ffmpeg-python opencc-python-reimplemented
还需要本地安装 ffmpeg: https://ffmpeg.org/download.html

用法:
    python make_subtitle.py input.mp4
"""

import os
import subprocess
import sys
import json
from pathlib import Path
from faster_whisper import WhisperModel
from opencc import OpenCC

# ======================
# 配置加载
# ======================
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"

DEFAULT_CONFIG = {
    "ffmpeg_path": r"F:\media\external_libs\ffmpeg\bin\ffmpeg.exe",
    "model_dir": str(BASE_DIR.parent / "models" / "faster-whisper-small"),
    "simplified": True,         # 是否转为简体中文
    "fontsize": 30,             # 字幕字号
    "fontname": "SimHei"        # 字体名称
}

if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        CONFIG = json.load(f)
else:
    CONFIG = DEFAULT_CONFIG
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
    print(f"⚠️ 未找到 config.json，已生成默认配置文件: {CONFIG_PATH}")


def format_timestamp(seconds: float) -> str:
    """转为 SRT 时间戳格式 00:00:00,000"""
    milliseconds = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def extract_audio(video_path: str, audio_path: str):
    """提取单声道 16kHz 音频"""
    cmd = [
        CONFIG["ffmpeg_path"], "-y",
        "-i", video_path,
        "-ar", "16000",
        "-ac", "1",
        audio_path
    ]
    subprocess.run(cmd, check=True)


def generate_srt(audio_path: str, srt_path: str):
    """调用 faster-whisper 生成字幕文件"""
    model = WhisperModel(CONFIG["model_dir"], device="cpu")

    cc = OpenCC("t2s") if CONFIG.get("simplified", False) else None

    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        task="transcribe",
        language="zh"
    )

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            start = format_timestamp(seg.start)
            end = format_timestamp(seg.end)
            text = seg.text.strip()
            if cc:
                text = cc.convert(text)
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

    print(f"✅ 已生成字幕文件: {srt_path}")


def burn_subtitles(video_path: str, srt_path: str, output_path: str):
    """用 ffmpeg 烧录字幕"""
    style = f"FontName={CONFIG['fontname']},Fontsize={CONFIG['fontsize']}"
    cmd = [
        CONFIG["ffmpeg_path"], "-y",
        "-i", video_path,
        "-vf", f"subtitles={srt_path}:force_style='{style}'",
        output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"🎬 已输出带字幕视频: {output_path}")


def main():
    os.makedirs("outputs", exist_ok=True)
    if len(sys.argv) < 2:
        print("用法: python make_subtitle.py <视频文件>")
        sys.exit(1)

    video_file = sys.argv[1]
    base = Path(video_file).stem
    audio_file = f"outputs/{base}_audio.wav"
    srt_file = f"outputs/{base}.srt"
    out_file = f"outputs/{base}_subtitled.mp4"

    extract_audio(video_file, audio_file)
    generate_srt(audio_file, srt_file)
    burn_subtitles(video_file, srt_file, out_file)


if __name__ == "__main__":
    main()
