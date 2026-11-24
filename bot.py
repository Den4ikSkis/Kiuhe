import asyncio
import re

import httpx
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from TTS.api import TTS

tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False)

MODEL = "hf.co/mradermacher/Qwen3.5-4B-SOMPOA-heresy-v2-GGUF:Q4_K_M"
SYSTEM_PROMPT = (
    "Ты — друг пользователя. Отвечай по-русски, дружелюбно, "
    "естественно и кратко, как живой собеседник. Без лишних формальностей."
)

ADDRESS_PATTERN = re.compile(r"(Киюха|Кирюха|Киюх|Кируха|Киуха)", re.IGNORECASE)


def ask_llm(text: str) -> str:
    try:
        r = httpx.post(
            "http://localhost:11434/api/chat",
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                "stream": False,
                "think": False,
                "options": {"num_ctx": 2048},
            },
            timeout=300,
        )
        r.raise_for_status()
        data = r.json()
        content = (data.get("message") or {}).get("content") or ""
        with open("llm_debug.log", "a", encoding="utf-8") as f:
            f.write(
                "REQ: %r\nDONE: %s  CONTENT_LEN: %d  CONTENT: %r\n\n"
                % (text, data.get("done_reason"), len(content), content[:300])
            )
        return content.strip()[:400]
    except Exception as e:
        with open("llm_debug.log", "a", encoding="utf-8") as f:
            f.write("ERROR: %r\n\n" % (e,))
        return f"Ошибка нейронки: {e}"


async def start(update: Update, context):
    msg = update.effective_message
    if msg:
        await msg.reply_text("Бот на голосе друга включен")


async def speak(update: Update, context):
    msg = update.effective_message
    if msg is None or not msg.text:
        return
    text = msg.text
    if not ADDRESS_PATTERN.search(text):
        return

    answer = await asyncio.to_thread(ask_llm, text)
    if not answer:
        answer = "Не понял тебя."
    answer = re.sub(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]", "", answer)

    await asyncio.to_thread(
        tts.tts_to_file,
        text=answer,
        file_path="voice.wav",
        speaker_wav="friend.wav",
        language="ru",
    )

    with open("voice.wav", "rb") as f:
        await msg.reply_voice(InputFile(f, "voice.wav"))


def main():
    app = Application.builder().token("9018344402:AAFVJOydI3MCuZoyAy0Wbm59kKdIS3aSUwQ").connect_timeout(90).read_timeout(90).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, speak))
    app.run_polling()


if __name__ == "__main__":
    main()
