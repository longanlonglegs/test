import base64
import flet as ft
import numpy as np
import asyncio
import os
import speech_recognition as sr
from gtts import gTTS
import io
import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks import python  
import asyncio

cap = None
ASLTSstate = False
STTstate = False
sttRecognizer = sr.Recognizer()
mic = sr.Microphone()

# Check if the model exists
model_path = os.path.join(os.path.dirname(__file__), 'asl.task')
#if not os.path.exists(model_path):
#raise FileNotFoundError(f"Model file not found at {model_path}")

# Create a GestureRecognizer object
asltsRecognizer = vision.GestureRecognizer.create_from_model_path(model_path)

async def main(page: ft.Page):

    page.adaptive = True

    page.title = "UpLink"

    data = io.BytesIO()

    # create a gTTS object
    gtts = gTTS(text="test", lang="en", slow=False)

    gtts.write_to_fp(data)

    data.seek(0)

    speech = base64.b64encode(data.read()).decode('utf-8')

    transcribedSpeechPlayer = ft.Audio(
        src_base64= speech
    )

    async def updateAudio(asl = ""):

        transcribedSpeechPlayer.release()

        try: gtts = gTTS(text=asl, lang="en", slow=False)
        except AssertionError: gtts = gTTS(text="space", lang="en", slow=False)

        data = io.BytesIO()

        gtts.write_to_fp(data)

        data.seek(0)

        speech = base64.b64encode(data.read()).decode('utf-8')

        transcribedSpeechPlayer.src_base64 = speech

        transcribedSpeechPlayer.update()
        transcribedSpeechPlayer.play()

        await asyncio.sleep(3)

        print(f"Generated audio for text: {asl}")

        # ... (rest of the existing code remains unchanged)

ft.app(main, assets_dir="assets")
