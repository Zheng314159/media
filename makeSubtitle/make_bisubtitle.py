#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_subtitle.py - 自动为视频生成中英文字幕并烧录到视频中（三文件模式，可选模式）
依赖:
    pip install faster-whisper ffmpeg-python opencc-python-reimplemented deep-translator
还需要本地安装 ffmpeg: https://ffmpeg.org/download.html

用法:
    python make_subtitle.py input.mp4 --mode all --burn
    python make_subtitle.py input.mp4 --mode all
    python make_subtitle.py input.mp4 --mode cn
    python make_subtitle.py input.mp4 --mode en
    python make_subtitle.py input.mp4 --mode ass
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from faster_whisper import WhisperModel
from opencc import OpenCC
from deep_translator import GoogleTranslator


# ======================
# 配置加载
# ======================
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"

DEFAULT_CONFIG = {
    "ffmpeg_path": r"F:\media\external_libs\ffmpeg\bin\ffmpeg.exe",
    "model_dir": str(BASE_DIR.parent / "models" / "faster-whisper-small"),
    "simplified": True,
    "fontsize_cn": 30,
    "fontsize_en": 18,
    "fontname": "SimHei"
}

if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        CONFIG = json.load(f)
else:
    CONFIG = DEFAULT_CONFIG
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
    print(f"⚠️ 未找到 config.json，已生成默认配置文件: {CONFIG_PATH}")

# 翻译缓存
CACHE_FILE = BASE_DIR / "outputs" / "translations.json"
if CACHE_FILE.exists():
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        TRANSLATION_CACHE = json.load(f)
else:
    TRANSLATION_CACHE = {}


def save_cache():
    os.makedirs("outputs", exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(TRANSLATION_CACHE, f, ensure_ascii=False, indent=2)


def translate(text_cn: str) -> str:
    """翻译中文 → 英文，带缓存"""
    if text_cn in TRANSLATION_CACHE:
        return TRANSLATION_CACHE[text_cn]
    try:
        text_en = GoogleTranslator(source="zh-CN", target="en").translate(text_cn)
    except Exception as e:
        print(f"[翻译异常] {text_cn} -> {e}")
        text_en = "[Translation Error]"
    TRANSLATION_CACHE[text_cn] = text_en
    return text_en


def format_timestamp_srt(seconds: float) -> str:
    """SRT 时间戳"""
    ms = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def format_timestamp_ass(seconds: float) -> str:
    """ASS 时间戳"""
    cs = int((seconds - int(seconds)) * 100)
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def extract_audio(video_path: str, audio_path: str):
    """提取音频"""
    cmd = [CONFIG["ffmpeg_path"], "-y", "-i", video_path, "-ar", "16000", "-ac", "1", audio_path]
    subprocess.run(cmd, check=True)


def generate_cn_srt(audio_path: str, srt_path: str):
    """生成中文字幕（自动切分，避免超长字幕）。对可能为 None 的时间戳做了安全处理。"""
    model = WhisperModel(CONFIG["model_dir"], device="cpu")
    cc = OpenCC("t2s") if CONFIG.get("simplified", False) else None

    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        task="transcribe",
        language="zh",
        word_timestamps=True,
    )

    MAX_CHARS = 15    # 每条字幕最多 15 个汉字（可调）
    MAX_DURATION = 5.0  # 每条字幕最长显示 5 秒（可调）

    def _to_float(x, fallback=0.0) -> float:
        # 明确把可能为 None 的值转换为 float（避免类型错误）
        return float(x) if x is not None else float(fallback)

    def split_text_by_punct_and_len(text: str, max_len: int):
        # 先按常见中文标点切分，若片段仍过长则硬切
        import re
        parts = re.split(r'[，。！？；；…\n]', text)
        out = []
        for p in parts:
            p = p.strip()
            if not p:
                continue
            if len(p) <= max_len:
                out.append(p)
            else:
                for i in range(0, len(p), max_len):
                    out.append(p[i:i+max_len])
        return out

    results = []
    idx = 1

    with open(srt_path, "w", encoding="utf-8") as f:
        for seg in segments:
            seg_start = _to_float(getattr(seg, "start", None), 0.0)
            seg_end = _to_float(getattr(seg, "end", None), seg_start)
            words = getattr(seg, "words", None) or []

            if words:
                buffer = ""
                start_time = None

                for w in words:
                    w_word = getattr(w, "word", "") or ""
                    text_piece = cc.convert(w_word.strip()) if cc else w_word.strip()
                    if not text_piece:
                        continue

                    w_start = _to_float(getattr(w, "start", None), seg_start)
                    w_end = _to_float(getattr(w, "end", None), w_start)

                    if start_time is None:
                        start_time = w_start

                    buffer += text_piece

                    duration = w_end - start_time
                    ends_with_punct = bool(buffer and buffer[-1] in "。！？!?.,;:，、；")

                    if len(buffer) >= MAX_CHARS or duration >= MAX_DURATION or ends_with_punct:
                        end_time = w_end
                        # 保证 end_time >= start_time
                        if end_time < start_time:
                            end_time = start_time + min(MAX_DURATION, max(0.1, seg_end - start_time))
                        f.write(f"{idx}\n{format_timestamp_srt(start_time)} --> {format_timestamp_srt(end_time)}\n{buffer}\n\n")
                        results.append((start_time, end_time, buffer))
                        idx += 1
                        buffer = ""
                        start_time = None

                # 残留 buffer（当前 segment 未 flush 的部分）
                if buffer:
                    end_time = seg_end if seg_end >= (start_time or seg_start) else (start_time or seg_start) + MAX_DURATION
                    f.write(f"{idx}\n{format_timestamp_srt(start_time or seg_start)} --> {format_timestamp_srt(end_time)}\n{buffer}\n\n")
                    results.append((start_time or seg_start, end_time, buffer))
                    idx += 1

            else:
                # 没有词级时间戳的回退处理：按标点/长度分片，并将 segment 时间均匀分配到各片段
                text = getattr(seg, "text", "").strip()
                if not text:
                    continue
                parts = split_text_by_punct_and_len(text, MAX_CHARS)
                seg_duration = max(seg_end - seg_start, 0.001)
                per = seg_duration / max(len(parts), 1)
                cur_start = seg_start
                for part in parts:
                    cur_end = cur_start + min(per, MAX_DURATION)
                    f.write(f"{idx}\n{format_timestamp_srt(cur_start)} --> {format_timestamp_srt(cur_end)}\n{part}\n\n")
                    results.append((cur_start, cur_end, part))
                    idx += 1
                    cur_start = cur_end

    print(f"✅ 已生成优化后的中文字幕: {srt_path}")
    return results



def generate_en_srt(cn_results, srt_path: str):
    """生成英文字幕"""
    print(f"🌐 开始翻译英文字幕...{cn_results}")
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, (start_sec, end_sec, text_cn) in enumerate(cn_results, 1):
            start = format_timestamp_srt(start_sec)
            end = format_timestamp_srt(end_sec)
            text_en = translate(text_cn)
            f.write(f"{i}\n{start} --> {end}\n{text_en}\n\n")
    print(f"✅ 已生成英文字幕: {srt_path}")

def load_srt(srt_path: str):
    """读取已有 SRT，返回 [(start_sec, end_sec, text)]"""
    results = []
    with open(srt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        if lines[i].strip().isdigit():
            # 时间轴
            time_line = lines[i+1].strip()
            start, end = time_line.split(" --> ")
            text = lines[i+2].strip()
            results.append((start, end, text))
            i += 4
        else:
            i += 1
    return results


def generate_en_srt_from_cn(cn_srt_path: str, en_srt_path: str):
    """读取已有 cn.srt，翻译生成 en.srt"""
    results = load_srt(cn_srt_path)
    with open(en_srt_path, "w", encoding="utf-8") as f:
        for idx, (start, end, text_cn) in enumerate(results, 1):
            text_en = translate(text_cn)
            f.write(f"{idx}\n{start} --> {end}\n{text_en}\n\n")
    print(f"✅ 已根据已有中文字幕生成英文字幕: {en_srt_path}")


def generate_ass(cn_results, ass_path: str):
    """合并生成双语字幕"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n\n")
        f.write("[V4+ Styles]\n")
        f.write(f"Style: CN,{CONFIG['fontname']},{CONFIG['fontsize_cn']},&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1\n")
        f.write(f"Style: EN,{CONFIG['fontname']},{CONFIG['fontsize_en']},&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,2,2,2,10,10,30,1\n\n")
        f.write("[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

        for start_sec, end_sec, text_cn in cn_results:
            start = format_timestamp_ass(start_sec)
            end = format_timestamp_ass(end_sec)
            text_en = translate(text_cn)
            f.write(f"Dialogue: 0,{start},{end},CN,,0,0,500,,{{\\c&H00FF00&}}{text_cn}\n")
            f.write(f"Dialogue: 0,{start},{end},EN,,0,0,400,,{{\\c&HFF0000&}}{text_en}\n")
    print(f"✅ 已生成双语字幕: {ass_path}")


def burn_subtitles(video_path: str, ass_path: str, output_path: str):
    """烧录字幕"""
    cmd = [CONFIG["ffmpeg_path"], "-y", "-i", video_path, "-vf", f"ass={ass_path}", output_path]
    subprocess.run(cmd, check=True)
    print(f"🎬 已输出带字幕视频: {output_path}")


def main():
    # 设置全局代理，deep-translator/requests 会自动读取
    os.environ["HTTP_PROXY"] = "http://127.0.0.1:1081"
    os.environ["HTTPS_PROXY"] = "http://127.0.0.1:1081"
    parser = argparse.ArgumentParser()
    parser.add_argument("video", help="输入视频文件")
    parser.add_argument("--mode", choices=["all", "cn", "en", "ass"], default="all", help="生成模式")
    parser.add_argument("--burn", action="store_true", help="是否烧录字幕到视频")
    parser.add_argument("--no-translate", action="store_true", help="只生成中文字幕")
    args = parser.parse_args()

    os.makedirs("outputs", exist_ok=True)
    base = Path(args.video).stem
    audio_file = f"outputs/{base}_audio.wav"
    cn_srt = f"outputs/{base}_cn.srt"
    en_srt = f"outputs/{base}_en.srt"
    ass_file = f"outputs/{base}.ass"
    out_file = f"outputs/{base}_subtitled.mp4"

    # 优先判断是否已存在cn.srt和en.srt，若都存在则直接合并生成ass
    cn_srt_exists = Path(cn_srt).exists()
    en_srt_exists = Path(en_srt).exists()
    cn_results = None

    if args.mode in ("ass", "all") and cn_srt_exists and en_srt_exists:
        # 直接读取cn.srt合并生成ass
        def parse_time(t):
            h,m,s_ms = t.split(":")
            s,ms = s_ms.split(",")
            return int(h)*3600+int(m)*60+int(s)+int(ms)/1000
        cn_results = []
        with open(cn_srt, "r", encoding="utf-8") as f:
            lines = f.readlines()
        i = 0
        while i < len(lines):
            if lines[i].strip().isdigit():
                time_line = lines[i+1].strip()
                start, end = time_line.split(" --> ")
                text = lines[i+2].strip()
                cn_results.append((parse_time(start), parse_time(end), text))
                i += 4
            else:
                i += 1
        generate_ass(cn_results, ass_file)
    else:
        # 只在需要时生成中文字幕
        if args.mode in ("all", "cn"):
            if not Path(cn_srt).exists():
                extract_audio(args.video, audio_file)
                cn_results = generate_cn_srt(audio_file, cn_srt)
            else:
                cn_results = None
        else:
            cn_results = None

        if not args.no_translate:
            if args.mode in ("all", "en"):
                if Path(en_srt).exists():
                    pass  # 已有英文字幕，跳过生成
                elif Path(cn_srt).exists():
                    generate_en_srt_from_cn(cn_srt, en_srt)
                else:
                    print("⚠️ 未找到 cn.srt，请先生成中文字幕！")
            if args.mode in ("all", "ass"):
                if Path(ass_file).exists():
                    pass  # 已有ass，跳过生成
                else:
                    # 生成ass时需要cn_results，如果没有则从srt加载
                    if cn_results is None and Path(cn_srt).exists():
                        def parse_time(t):
                            h,m,s_ms = t.split(":")
                            s,ms = s_ms.split(",")
                            return int(h)*3600+int(m)*60+int(s)+int(ms)/1000
                        cn_results = []
                        with open(cn_srt, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                        i = 0
                        while i < len(lines):
                            if lines[i].strip().isdigit():
                                time_line = lines[i+1].strip()
                                start, end = time_line.split(" --> ")
                                text = lines[i+2].strip()
                                cn_results.append((parse_time(start), parse_time(end), text))
                                i += 4
                            else:
                                i += 1
                    if cn_results:
                        generate_ass(cn_results, ass_file)
                    else:
                        print("⚠️ 未找到 cn.srt，无法生成ass字幕！")

    # ========== 烧录字幕 ========== 
    if args.burn:
        if args.mode == "cn":
            # 烧录中文字幕
            if Path(cn_srt).exists():
                # 先将cn.srt转ass
                def parse_time(t):
                    h,m,s_ms = t.split(":")
                    s,ms = s_ms.split(",")
                    return int(h)*3600+int(m)*60+int(s)+int(ms)/1000
                cn_results = []
                with open(cn_srt, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                i = 0
                while i < len(lines):
                    if lines[i].strip().isdigit():
                        time_line = lines[i+1].strip()
                        start, end = time_line.split(" --> ")
                        text = lines[i+2].strip()
                        cn_results.append((parse_time(start), parse_time(end), text))
                        i += 4
                    else:
                        i += 1
                # 只生成中文ass
                ass_path = f"outputs/{base}_cn.ass"
                with open(ass_path, "w", encoding="utf-8") as f:
                    f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n\n")
                    f.write("[V4+ Styles]\n")
                    f.write(f"Style: CN,{CONFIG['fontname']},{CONFIG['fontsize_cn']},&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,2,2,2,10,10,40,1\n\n")
                    f.write("[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
                    for start_sec, end_sec, text_cn in cn_results:
                        start = format_timestamp_ass(start_sec)
                        end = format_timestamp_ass(end_sec)
                        f.write(f"Dialogue: 0,{start},{end},CN,,0,0,120,,{{\\c&H00FF00&}}{text_cn}\n")
                burn_subtitles(args.video, ass_path, out_file)
            else:
                print("⚠️ 未找到 cn.srt，无法烧录中文字幕！")
        elif args.mode == "en":
            # 烧录英文字幕
            if Path(en_srt).exists():
                # 先将en.srt转ass
                def parse_time(t):
                    h,m,s_ms = t.split(":")
                    s,ms = s_ms.split(",")
                    return int(h)*3600+int(m)*60+int(s)+int(ms)/1000
                en_results = []
                with open(en_srt, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                i = 0
                while i < len(lines):
                    if lines[i].strip().isdigit():
                        time_line = lines[i+1].strip()
                        start, end = time_line.split(" --> ")
                        text = lines[i+2].strip()
                        en_results.append((parse_time(start), parse_time(end), text))
                        i += 4
                    else:
                        i += 1
                # 只生成英文ass
                ass_path = f"outputs/{base}_en.ass"
                with open(ass_path, "w", encoding="utf-8") as f:
                    f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n\n")
                    f.write("[V4+ Styles]\n")
                    f.write(f"Style: EN,{CONFIG['fontname']},{CONFIG['fontsize_en']},&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,2,2,2,10,10,20,1\n\n")
                    f.write("[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
                    for start_sec, end_sec, text_en in en_results:
                        start = format_timestamp_ass(start_sec)
                        end = format_timestamp_ass(end_sec)
                        f.write(f"Dialogue: 0,{start},{end},EN,,0,0,80,,{{\\c&HFF0000&}}{text_en}\n")
                burn_subtitles(args.video, ass_path, out_file)
            else:
                print("⚠️ 未找到 en.srt，无法烧录英文字幕！")
        elif args.mode in ("all", "ass"):
            if Path(ass_file).exists():
                burn_subtitles(args.video, ass_file, out_file)
            else:
                print("⚠️ 未找到 ass 文件，无法烧录中英文字幕！")

    save_cache()


if __name__ == "__main__":
    main()
