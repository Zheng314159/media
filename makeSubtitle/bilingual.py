#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_subtitle.py - 自动为视频生成字幕并烧录到视频中（支持手动修改后再合并的中英双语流程）

依赖:
    pip install faster-whisper ffmpeg-python opencc-python-reimplemented
还需要本地安装 ffmpeg: https://ffmpeg.org/download.html

用法（逐步）:
  1) 提取音频:
     python make_subtitle.py extract <video.mp4>
     -> 生成 <video>_audio.wav

  2) 生成中文字幕（可选简体转换，生成后可手动修改）:
     python make_subtitle.py gen-zh <video>_audio.wav
     -> 生成 <video>_zh.srt

  3) 生成英文字幕（英文翻译）:
     python make_subtitle.py gen-en <video>_audio.wav
     -> 生成 <video>_en.srt

  4) （可选）手动打开 <video>_zh.srt 修改中文内容，但**不要改动时间轴**更稳妥

  5) 合并中英为双语 SRT（中文在上，英文在下）:
     python make_subtitle.py merge <video>_zh.srt <video>_en.srt
     -> 生成 <video>_bi.srt

  6) 烧录双语字幕到视频:
     python make_subtitle.py burn <video.mp4> <video>_bi.srt
     -> 生成 <video>_subtitled.mp4
"""

import re
import subprocess
import sys
import json
from pathlib import Path
from typing import List, Tuple, Optional
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
    "simplified": True,         # 是否把中文字幕转为简体中文
    "fontsize": 30,             # 字幕字号（SRT 全部统一大小）
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


# ======================
# 时间戳工具
# ======================
def format_timestamp(seconds: float) -> str:
    """转为 SRT 时间戳格式 00:00:00,000"""
    milliseconds = int(round((seconds - int(seconds)) * 1000))
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def parse_timestamp(ts: str) -> float:
    """SRT 时间戳 00:00:00,000 -> 秒"""
    h, m, rest = ts.split(":")
    s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


# ======================
# SRT 读写
# ======================
class SRTEntry:
    def __init__(self, idx: int, start: float, end: float, text: str):
        self.idx = idx
        self.start = start
        self.end = end
        self.text = text  # 允许多行


def read_srt(path: str) -> List[SRTEntry]:
    content = Path(path).read_text(encoding="utf-8", errors="ignore")
    # 去掉 UTF-8 BOM
    content = content.lstrip("\ufeff")
    blocks = re.split(r"\n{2,}", content.strip())
    entries: List[SRTEntry] = []
    for b in blocks:
        lines = [ln for ln in b.splitlines() if ln.strip() != "" or True]
        if len(lines) < 2:
            continue
        # 第一行可能是序号
        idx_line = lines[0].strip()
        idx = None
        if re.fullmatch(r"\d+", idx_line):
            idx = int(idx_line)
            time_line_i = 1
        else:
            # 没有序号的 SRT（少见），尝试从行0读取时间
            time_line_i = 0
            idx = len(entries) + 1

        time_line = lines[time_line_i].strip()
        m = re.match(r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})", time_line)
        if not m:
            continue
        start = parse_timestamp(m.group(1))
        end = parse_timestamp(m.group(2))

        text_lines = lines[time_line_i + 1 :]
        text = "\n".join(text_lines).strip()
        entries.append(SRTEntry(idx, start, end, text))
    return entries


def write_srt(entries: List[SRTEntry], path: str):
    with open(path, "w", encoding="utf-8") as f:
        for i, e in enumerate(entries, 1):
            f.write(f"{i}\n{format_timestamp(e.start)} --> {format_timestamp(e.end)}\n{e.text}\n\n")


# ======================
# 影音处理
# ======================
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
    print(f"🎧 已提取音频: {audio_path}")


# ======================
# 模型调用（独立步骤）
# ======================
def load_model() -> WhisperModel:
    return WhisperModel(CONFIG["model_dir"], device="cpu")


def generate_zh_srt(audio_path: str, zh_srt_path: str, language: str = "zh"):
    """生成中文字幕（可按配置转简体），仅中文一行"""
    model = load_model()
    cc = OpenCC("t2s") if CONFIG.get("simplified", False) else None

    segments, _ = model.transcribe(
        audio_path,
        beam_size=5,
        task="transcribe",
        language=language
    )

    entries: List[SRTEntry] = []
    for i, seg in enumerate(segments, 1):
        text = seg.text.strip()
        if cc:
            text = cc.convert(text)
        entries.append(SRTEntry(i, seg.start, seg.end, text))

    write_srt(entries, zh_srt_path)
    print(f"✅ 已生成中文字幕: {zh_srt_path}")


def generate_en_srt(audio_path: str, en_srt_path: str, source_language: str = "zh"):
    """生成英文字幕（Whisper 翻译），仅英文一行"""
    model = load_model()
    segments, _ = model.transcribe(
        audio_path,
        beam_size=5,
        task="translate",
        language=source_language
    )

    entries: List[SRTEntry] = []
    for i, seg in enumerate(segments, 1):
        text = seg.text.strip()
        entries.append(SRTEntry(i, seg.start, seg.end, text))

    write_srt(entries, en_srt_path)
    print(f"✅ 已生成英文字幕: {en_srt_path}")


# ======================
# 合并（独立步骤）
# ======================
def align_segments_by_time(
    zh: List[SRTEntry],
    en: List[SRTEntry],
    tolerance: float = 1.0
) -> List[Tuple[SRTEntry, Optional[SRTEntry]]]:
    """
    将中文段落与英文段落按起始时间近似对齐。
    - 优先一一配对（避免重复使用英文条目）
    - 若找不到合适英文，英文为 None（会只输出中文行）
    提示：如果你没有改动中文字幕的时间轴，通常长度一致，此步骤只是兜底。
    """
    result: List[Tuple[SRTEntry, Optional[SRTEntry]]] = []
    used = [False] * len(en)
    j = 0
    for z in zh:
        best_idx = None
        best_diff = float("inf")
        # 限制搜索窗口提高速度
        for k in range(j, min(j + 10, len(en))):
            if used[k]:
                continue
            diff = abs(en[k].start - z.start)
            if diff < best_diff:
                best_diff = diff
                best_idx = k
                if best_diff <= tolerance:
                    break
        if best_idx is not None:
            result.append((z, en[best_idx]))
            used[best_idx] = True
            j = best_idx + 1
        else:
            result.append((z, None))
    return result


def merge_bilingual_srt(zh_srt_path: str, en_srt_path: str, out_path: str):
    """
    合并为双语 SRT：中文在上，英文在下。
    - 默认按时间对齐（更稳），如果条目数量一致且时间基本一致，其实等价于按索引对齐。
    - 如果某条没有英文匹配，会只写中文行。
    """
    zh_entries = read_srt(zh_srt_path)
    en_entries = read_srt(en_srt_path)

    pairs = align_segments_by_time(zh_entries, en_entries, tolerance=1.0)

    merged: List[SRTEntry] = []
    for i, (zh, en) in enumerate(pairs, 1):
        # 采用中文时间轴为准；若英文存在但更长，你也可以按需改为 max()
        start = zh.start
        end = zh.end
        if en is not None:
            text = f"{zh.text}\n{en.text}"
        else:
            text = zh.text
        merged.append(SRTEntry(i, start, end, text))

    write_srt(merged, out_path)
    print(f"🈴 已合并双语字幕: {out_path}")


# ======================
# 烧录（独立步骤）
# ======================
def _escape_for_ffmpeg_subtitles(path: str) -> str:
    """
    处理 Windows 路径在 subtitles 滤镜中的转义:
    - 反斜杠 -> 双反斜杠
    - 盘符冒号 -> '\:'
    - 单引号 -> '\''
    """
    p = path.replace("\\", "\\\\")
    # 只替换盘符处的冒号，如 C:\  -> C\:
    if re.match(r"^[A-Za-z]:", path):
        p = p.replace(":", r"\:", 1)
    p = p.replace("'", r"\'")
    return p


def burn_subtitles(video_path: str, srt_path: str, output_path: str):
    """用 ffmpeg 烧录字幕（SRT 统一样式）"""
    style = f"FontName={CONFIG['fontname']},Fontsize={CONFIG['fontsize']}"
    srt_escaped = _escape_for_ffmpeg_subtitles(str(Path(srt_path).resolve()))
    vf = f"subtitles='{srt_escaped}':force_style='{style}'"

    cmd = [
        CONFIG["ffmpeg_path"], "-y",
        "-i", video_path,
        "-vf", vf,
        output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"🎬 已输出带字幕视频: {output_path}")


# ======================
# 命令行入口（每一步可单独执行）
# ======================
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    sub = sys.argv[1].lower()

    if sub == "extract":
        if len(sys.argv) < 3:
            print("用法: python make_subtitle.py extract <video.mp4>")
            sys.exit(1)
        video = sys.argv[2]
        base = Path(video).with_suffix("")
        audio = f"{base}_audio.wav"
        extract_audio(video, audio)

    elif sub == "gen-zh":
        if len(sys.argv) < 3:
            print("用法: python make_subtitle.py gen-zh <audio.wav>")
            sys.exit(1)
        audio = sys.argv[2]
        base = Path(audio).with_suffix("")
        zh_srt = f"{base}_zh.srt"
        generate_zh_srt(audio, zh_srt)

    elif sub == "gen-en":
        if len(sys.argv) < 3:
            print("用法: python make_subtitle.py gen-en <audio.wav>")
            sys.exit(1)
        audio = sys.argv[2]
        base = Path(audio).with_suffix("")
        en_srt = f"{base}_en.srt"
        generate_en_srt(audio, en_srt)

    elif sub == "merge":
        if len(sys.argv) < 4:
            print("用法: python make_subtitle.py merge <zh.srt> <en.srt>")
            sys.exit(1)
        zh_srt = sys.argv[2]
        en_srt = sys.argv[3]
        # 输出名按中文 SRT 命名
        base = Path(zh_srt).with_suffix("")
        out = f"{base}_bi.srt"
        merge_bilingual_srt(zh_srt, en_srt, out)

    elif sub == "burn":
        if len(sys.argv) < 4:
            print("用法: python make_subtitle.py burn <video.mp4> <bilingual.srt>")
            sys.exit(1)
        video = sys.argv[2]
        srt = sys.argv[3]
        base = Path(video).with_suffix("")
        out = f"{base}_subtitled.mp4"
        burn_subtitles(video, srt, out)

    else:
        print("未知命令。可用命令: extract | gen-zh | gen-en | merge | burn")
        sys.exit(1)


if __name__ == "__main__":
    main()
