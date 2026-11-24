from TTS.api import TTS
import playsound

tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False)

tts.tts_to_file(
    text="Привет! Как твои дела?",
    file_path="voice.wav",
    speaker_wav="friend.wav",
    language="ru",
)

playsound.playsound("voice.wav")