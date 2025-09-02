# 文件名: tts_video.py
import os
from TTS.api import TTS
from TTS.utils.manage import ModelManager
from moviepy import VideoFileClip, AudioFileClip
from TTS.utils.synthesizer import Synthesizer
from TTS.utils.radam import RAdam
import torch
import collections

def init_synthesizer(model_dir: str, use_cuda: bool = False):
    """
    初始化 TTS Synthesizer
    """
        # manager = ModelManager()
    # print(manager.list_models())  # 输出所有可用模型
    print("[INFO] 正在生成语音...")
    torch.serialization.add_safe_globals([RAdam])
    torch.serialization.add_safe_globals([collections.defaultdict])
    torch.serialization.add_safe_globals([dict])
    config_path = os.path.join(model_dir, "config.json")
    model_path = os.path.join(model_dir, "model_file.pth")
    stats_path = os.path.join(model_dir, "scale_stats.npy")

    synthesizer = Synthesizer(
        tts_checkpoint=model_path,
        tts_config_path=config_path,
        use_cuda=use_cuda
    )
    return synthesizer


def tts_to_file(synthesizer, text: str, output_path: str):
    """
    将文字转成语音文件
    """
    if output_path is None:
        output_path = "feoutput/output.wav"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    wav = synthesizer.tts(text)  # 自动根据文本生成时长
    synthesizer.save_wav(wav, output_path)
    print(f"✅ 已生成语音文件: {output_path}")


if __name__ == "__main__":
    model_dir = r"F:\media\models\tacotron2-DDC-GST"  # 你的模型目录
    synthesizer = init_synthesizer(model_dir, use_cuda=False)

    text = "大家好，欢迎收看本期视频！"
    output_path = "feoutput/output.wav"

    tts_to_file(synthesizer, text, output_path)
