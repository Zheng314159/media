import collections
import os
import subprocess
import tempfile
from pathlib import Path

import torch
from TTS.api import TTS
from TTS.config.shared_configs import BaseDatasetConfig
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import XttsArgs, XttsAudioConfig
from TTS.utils.radam import RAdam
from faster_whisper import WhisperModel


class MediaProcessor:
    def __init__(self, ffmpeg_path: str, tts_model_dir: str, asr_model_dir: str, device: str = "cuda"):
        self.ffmpeg_path = ffmpeg_path
        self.tts_model_dir = tts_model_dir
        self.asr_model_dir = Path(asr_model_dir)
        self.device = device
        self.model = None
        self.clean_speaker = None

        # 注册 Coqui TTS 必要的安全 globals
        os.environ["COQUI_TOS_AGREED"] = "1"
        torch.serialization.add_safe_globals([RAdam])
        torch.serialization.add_safe_globals([collections.defaultdict])
        torch.serialization.add_safe_globals([dict])
        torch.serialization.add_safe_globals([XttsConfig])
        torch.serialization.add_safe_globals([XttsAudioConfig])
        torch.serialization.add_safe_globals([BaseDatasetConfig])
        torch.serialization.add_safe_globals([XttsArgs])

    # -------------------------
    # TTS 模型加载
    # -------------------------
    def load_model(self, force_reload: bool = False):
        if self.model is None or force_reload:
            print("🔄 Loading XTTS model...")
            self.model = TTS(
                model_path=self.tts_model_dir,
                config_path=os.path.join(self.tts_model_dir, "config.json"),
                progress_bar=False
            ).to(self.device)
            print("✅ Model loaded.")
        return self.model

    # -------------------------
    # 设置说话人
    # -------------------------
    def set_speaker(self, speaker_file: str, cleanup_voice: bool = True, save_path: str | None = None):
        if save_path is None:
            save_path = "speakers/clean_speaker.wav"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        filter_ = "highpass=75,lowpass=8000,"
        trim_silence = (
            "areverse,silenceremove=start_periods=1:start_silence=0:start_threshold=0.02,"
            "areverse,silenceremove=start_periods=1:start_silence=0:start_threshold=0.02"
        )

        if cleanup_voice:
            cmd = f"{self.ffmpeg_path} -i \"{speaker_file}\" -af {filter_}{trim_silence} -y \"{save_path}\""
        else:
            cmd = f"{self.ffmpeg_path} -i \"{speaker_file}\" -y \"{save_path}\""
        os.system(cmd)

        self.clean_speaker = save_path
        print(f"🎙️ Speaker set and preprocessed: {self.clean_speaker}")
        return self.clean_speaker

    # -------------------------
    # 语音合成（支持 txt 文件）
    # -------------------------
    def speak(self, text: str, output_path: str, language: str = "zh"):
        if not self.clean_speaker:
            raise ValueError("❌ 请先调用 set_speaker() 设置说话人")

        # 如果 text 是一个 txt 文件路径，读取内容
        if os.path.isfile(text) and text.lower().endswith(".txt"):
            with open(text, "r", encoding="utf-8") as f:
                text = f.read().strip()

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        model = self.load_model()

        print("🗣️ Synthesizing speech...")
        model.tts_to_file(
            text=text,
            file_path=output_path,
            speaker_wav=self.clean_speaker,
            language=language
        )
        print(f"✅ Speech synthesized successfully: {output_path}")

    # -------------------------
    # 工具: 格式化 SRT 时间戳
    # -------------------------
    @staticmethod
    def format_timestamp(seconds: float) -> str:
        milliseconds = int((seconds - int(seconds)) * 1000)
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

    # -------------------------
    # 工具: 提取音频
    # -------------------------
    def extract_audio(self, video_path: str, audio_path: str):
        cmd = [
            self.ffmpeg_path, "-y",
            "-i", video_path,
            "-ar", "16000",  # 采样率
            "-ac", "1",      # 单声道
            audio_path
        ]
        subprocess.run(cmd, check=True)

    # -------------------------
    # ASR: 生成字幕文件
    # -------------------------
    def generate_srt(self, audio_path: str, srt_path: str, beam_size: int = 5):
        model = WhisperModel(str(self.asr_model_dir.resolve()), device="cpu")
        segments, info = model.transcribe(audio_path, beam_size=beam_size)

        with open(srt_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments, 1):
                start = self.format_timestamp(seg.start)
                end = self.format_timestamp(seg.end)
                text = seg.text.strip()
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

        print(f"✅ 已生成字幕文件: {srt_path}")
        return srt_path

    # -------------------------
    # 烧录字幕
    # -------------------------
    def burn_subtitles(self, video_path: str, srt_path: str, output_path: str):
        cmd = [
            self.ffmpeg_path, "-y",
            "-i", video_path,
            "-vf", f"subtitles={srt_path}:force_style='Fontsize=24'",
            output_path
        ]
        subprocess.run(cmd, check=True)
        print(f"🎬 已输出带字幕视频: {output_path}")