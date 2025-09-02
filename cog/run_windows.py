import collections
import os
import tempfile

import torch
from TTS.api import TTS
from TTS.config.shared_configs import BaseDatasetConfig
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import XttsArgs, XttsAudioConfig
from TTS.utils.radam import RAdam

# --- Configuration ---
INPUT_TEXT_FILE = "input.txt"
SPEAKER_FILE = "4.MOV"
OUTPUT_WAV_FILE = "outputs/result.wav"
LANGUAGE = "zh" 
FFMPEG_PATH = r"F:\media\external_libs\ffmpeg\bin\ffmpeg.exe"

def main():
    """Main function to run the TTS prediction."""
    
    # Set environment variable for Coqui TTS
    os.environ["COQUI_TOS_AGREED"] = "1"
    torch.serialization.add_safe_globals([RAdam])
    torch.serialization.add_safe_globals([collections.defaultdict])
    torch.serialization.add_safe_globals([dict])
    torch.serialization.add_safe_globals([XttsConfig])
    torch.serialization.add_safe_globals([XttsAudioConfig])
    torch.serialization.add_safe_globals([BaseDatasetConfig])
    torch.serialization.add_safe_globals([XttsArgs])
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(OUTPUT_WAV_FILE)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load the TTS model
    print("Loading TTS model from local path...")
    model_dir = r"F:\media\models\XTTS-v2"
    model = TTS(
        model_path=model_dir,
        config_path=os.path.join(model_dir, "config.json"),
        progress_bar=False
    ).to('cuda')
    print("Model loaded.")

    # Read the input text
    with open(INPUT_TEXT_FILE, "r", encoding="utf-8") as f:
        text = f.read().strip()
    
    print(f"Input text: {text}")

    # Create temporary files for speaker and output wav
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_speaker_wav:
        speaker_wav_path = temp_speaker_wav.name

    print(f"Converting speaker file to wav: {speaker_wav_path}")
    os.system(f"{FFMPEG_PATH} -i {SPEAKER_FILE} -y {speaker_wav_path}")

    # Run the TTS model
    print("Synthesizing speech...")
    model.tts_to_file(
        text=text,
        file_path=OUTPUT_WAV_FILE,
        speaker_wav=speaker_wav_path,
        language=LANGUAGE
    )

    # Clean up temporary file
    os.remove(speaker_wav_path)

    print(f"✅ Speech synthesized successfully: {OUTPUT_WAV_FILE}")

if __name__ == "__main__":
    main()
