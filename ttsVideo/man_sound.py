from core.processor import MediaProcessor


if __name__ == "__main__":
    processor = MediaProcessor(
        ffmpeg_path=r"F:\media\external_libs\ffmpeg\bin\ffmpeg.exe",
        tts_model_dir=r"F:\media\models\XTTS-v2",
        asr_model_dir=r"F:\media\models\faster-whisper-small",
        device="cuda"
    )

    # 设置说话人
    processor.set_speaker("sample/4.MOV")

    # 合成（字符串输入）
    processor.speak("你好，这是第一段合成语音。", "outputs/result1.wav")

    # 合成（txt 文件输入）
    processor.speak("input.txt", "outputs/result2.wav")

    # 提取音频 + 语音转文字
    processor.extract_audio("sample/4.MOV", "outputs/audio.wav")
    processor.generate_srt("outputs/audio.wav", "outputs/subtitles.srt")
    processor.burn_subtitles("sample/4.MOV", "outputs/subtitles.srt", "outputs/video_with_subs.mp4")
