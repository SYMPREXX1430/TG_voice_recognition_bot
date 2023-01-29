from moviepy.editor import AudioFileClip
import os

class AudioFileClipWithDelete(AudioFileClip):
    def __init__(self, wav_file, *args, **kwargs):
        self.wav_file = wav_file
        super().__init__(wav_file, *args, **kwargs)

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)
        os.remove(self.wav_file)