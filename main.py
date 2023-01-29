from auth_data import token
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
import asyncio
import os
from pathlib import Path
import speech_recognition
import datetime
from moviepy.editor import VideoFileClip, AudioFileClip
import torch
from logger import get_logger
from auxiliary_classes import AudioFileClipWithDelete

bot = Bot(token)
dp = Dispatcher(bot)
sr = speech_recognition.Recognizer()
logger = get_logger('main')


@dp.message_handler(commands=["info"])
async def cmd_start(message: types.Message):
    await message.answer("Бот создан для распознавания текста из голосовых и видеосообщений.")


@dp.message_handler(content_types=[
    types.ContentType.VOICE,
    types.ContentType.VIDEO_NOTE])
async def reply(message: types.Message):
    if message.content_type == types.ContentType.VOICE:
        file_id = message.voice.file_id
        file_type = 'voice'
    elif message.content_type == types.ContentType.VIDEO_NOTE:
        file_id = message.video_note.file_id
        file_type = 'video'

    try:
        raw_text = await download_and_recognize(file_id, file_type)
        text = await asyncio.to_thread(restore_punctuation, raw_text)
    except speech_recognition.UnknownValueError:
        text = 'Не удалось распознать текст'
        logger.error(f'{datetime.datetime.today().strftime("%H:%M:%S")}_{message.from_user.id}_'
                     f'{message.from_user.first_name}_{message.from_user.last_name}_'
                     f'{message.from_user.username} Err: NoVoiceRecognized  \n')
    except Exception as e:
        text = 'Неизвестная ошибка. Разработчик обязательно посмотрит логи и все исправит.'
        logger.error(f'{datetime.datetime.today().strftime("%H:%M:%S")}_{message.from_user.id}_'
                     f'{message.from_user.first_name}_{message.from_user.last_name}_'
                     f'{message.from_user.username} Err: {e}  \n')

    if len(text) > 4096:
        for x in range(0, len(text), 4096):
            await message.reply(text[x:x + 4096])
    else:
        await message.reply(text)


def convert_to_wav(f_id, temp_file_path, file_type):
    wav_on_disk = f'{f_id}.wav'
    if file_type == 'voice':
        with AudioFileClip(f"{f_id}.oga") as audioclip:
            audioclip.write_audiofile(f"{f_id}.wav")
    else:
        with VideoFileClip(f"{f_id}.mp4") as videoclip:
            audioclip = videoclip.audio
            audioclip.write_audiofile(f"{f_id}.wav")
    os.remove(temp_file_path)
    return wav_on_disk


def restore_punctuation(raw_text):
    try:
        model, example_texts, languages, punct, apply_te = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                                                      model='silero_te')
        text = apply_te(raw_text.lower(), lan='ru')
    except IndexError:
        text = raw_text
    return text


def split_recognize(f_id, wav):
    with AudioFileClip(wav) as audioclip:
        audio_duration = audioclip.duration
        start_timestamps = [i for i in range(0, int(audio_duration), 200)]
        finish_timestamps = [i for i in range(200, int(audio_duration), 200)]
        finish_timestamps.append(audio_duration)

        temp_file_names = [f'{f_id}_{x + 1}.wav' for x in range(len(start_timestamps))]

        subclips = [audioclip.subclip(start_timestamps_value, finish_timestaps_value)
                    for start_timestamps_value, finish_timestaps_value in zip(start_timestamps, finish_timestamps)]

        for name, subclip in zip(temp_file_names, subclips):
            subclip.write_audiofile(name)

    text = ''
    for voice_shard in temp_file_names:
        wav_recognized = speech_recognition.AudioFile(voice_shard)
        with wav_recognized as source:
            sr.adjust_for_ambient_noise(source, duration=0.01)
            audio = sr.record(source)
        text = text + "" + sr.recognize_google(audio_data=audio, language='ru-RU')
        os.remove(voice_shard)

    return text


async def download_and_recognize(f_id, file_type):
    file = await bot.get_file(f_id)
    file_path = file.file_path
    if file_type == 'voice':
        file_on_disk = Path("", f"{f_id}.oga")
    else:
        file_on_disk = Path("", f"{f_id}.mp4")
    await bot.download_file(file_path, destination=file_on_disk)

    wav_on_disk = await asyncio.to_thread(convert_to_wav, f_id, file_on_disk, file_type)

    with AudioFileClipWithDelete(wav_on_disk) as audioclip:
        audio_duration = audioclip.duration
        if audio_duration > 200:
            text = await asyncio.to_thread(split_recognize, f_id, wav_on_disk)
        else:
            wav_recognized = speech_recognition.AudioFile(wav_on_disk)
            with wav_recognized as source:
                sr.adjust_for_ambient_noise(source, duration=0.3)
                audio = sr.record(source)
            text = sr.recognize_google(audio_data=audio, language='ru-RU')

    return text


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
