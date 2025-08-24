#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_subtitle.py - 自动为视频生成字幕并烧录到视频中
依赖: pip install faster-whisper ffmpeg-python
还需要本地安装 ffmpeg: https://ffmpeg.org/download.html
python make_subtitle.py input.mp4

python make_subtitle.py input.mp4 --voice sample.wav
"""

import subprocess
import sys
import os
from pathlib import Path
from faster_whisper import WhisperModel
from resemblyzer import VoiceEncoder, preprocess_wav
from TTS.api import TTS
import torch

FFMPEG_PATH=r"F:\media\external_libs\ffmpeg\bin\ffmpeg.exe"
MODEL_DIR = Path(__file__).resolve().parent.parent / "models" / "faster-whisper-small"
TTS_MODEL_PATH = r"F:\media\models\XTTS-v2"

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
        FFMPEG_PATH, "-y",
        "-i", video_path,
        "-ar", "16000",
        "-ac", "1",
        audio_path
    ]
    subprocess.run(cmd, check=True)


def generate_srt(audio_path: str, srt_path: str, model_size="small"):
    """调用 faster-whisper 生成字幕文件"""
    # 模型路径（相对路径，基于 make_subtitle.py 所在目录）
    model = WhisperModel(str(MODEL_DIR.resolve()), device="cpu")

    segments, info = model.transcribe(audio_path, beam_size=5)
    text_segments = []
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            start = format_timestamp(seg.start)
            end = format_timestamp(seg.end)
            text = seg.text.strip()
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
            text_segments.append(text)
    print(f"✅ 已生成字幕文件: {srt_path}")
    return text_segments


def burn_subtitles(video_path: str, srt_path: str, output_path: str):
    """用 ffmpeg 烧录字幕"""
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", video_path,
        "-vf", f"subtitles={srt_path}:force_style='Fontsize=24'",
        output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"🎬 已输出带字幕视频: {output_path}")


def clone_voice_and_tts(texts, voice_sample, output_path):
    """用 XTTS v2 声纹克隆并生成配音（CPU 优化版）"""
    print("🗣 开始克隆声音并朗读字幕...")

    tts = TTS(model_path=TTS_MODEL_PATH, gpu=False)

    # 输出合成的临时片段
    tmp_dir = Path("tmp_segments")
    tmp_dir.mkdir(exist_ok=True)

    segment_files = []
    for i, text in enumerate(texts, 1):
        seg_file = tmp_dir / f"seg_{i:03d}.wav"
        if text.strip():
            tts.tts_to_file(
                text=text,
                speaker_wav=voice_sample,
                language="zh-cn",
                file_path=str(seg_file)
            )
            segment_files.append(seg_file)

    # 用 ffmpeg 拼接所有片段
    list_file = tmp_dir / "segments.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for seg in segment_files:
            f.write(f"file '{seg.as_posix()}'\n")

    cmd = [
        FFMPEG_PATH, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        output_path
    ]
    subprocess.run(cmd, check=True)

    print(f"✅ 已生成配音文件: {output_path}")



def main():
    if len(sys.argv) < 2:
        print("用法: python make_subtitle_voice.py <视频文件> [--voice sample.wav]")
        sys.exit(1)

    video_file = sys.argv[1]
    voice_sample = None
    if "--voice" in sys.argv:
        idx = sys.argv.index("--voice")
        if idx + 1 < len(sys.argv):
            voice_sample = sys.argv[idx + 1]

    base = Path(video_file).stem
    audio_file = f"{base}_audio.wav"
    srt_file = f"{base}.srt"
    out_file = f"{base}_subtitled.mp4"
    dub_file = f"{base}_dubbed.wav"

    extract_audio(video_file, audio_file)
    texts = generate_srt(audio_file, srt_file)
    burn_subtitles(video_file, srt_file, out_file)

    if voice_sample:
        clone_voice_and_tts(texts, voice_sample, dub_file)


if __name__ == "__main__":
    main()
