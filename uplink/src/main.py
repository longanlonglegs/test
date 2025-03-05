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
STTstate = False
recognizer = None

async def main(page: ft.Page):

    page.adaptive = True

    page.title = "UpLink"

    # Language in which you want to convert
    language = 'en'

    async def add_tts(e):
        await a(e)

    async def a(e):
        # Generate the audio in memory
        myobj = gTTS(text=e.control.value, lang=language, slow=False)
        audio_bytes = io.BytesIO()
        myobj.write_to_fp(audio_bytes)
        audio_bytes.seek(0)  # Reset the stream position to the beginning

        # Convert the audio to a base64-encoded string
        audio_base64 = base64.b64encode(audio_bytes.read()).decode("utf-8")

        # Update the audio source and play
        audio1.src = None
        audio1.src_base64 = audio_base64
        audio1.update()
        audio1.play()

    async def a_final(e):
        # Generate the audio in memory
        myobj = gTTS(text=e, lang=language, slow=False)
        audio_bytes = io.BytesIO()
        myobj.write_to_fp(audio_bytes)
        audio_bytes.seek(0)  # Reset the stream position to the beginning

        # Convert the audio to a base64-encoded string
        audio_base64 = base64.b64encode(audio_bytes.read()).decode("utf-8")

        # Update the audio source and play
        audio1.src = None
        audio1.src_base64 = audio_base64
        audio1.update()
        audio1.play()

    audio1 = ft.Audio(
        src="https://luan.xyz/files/audio/ambient_c_motion.mp3"
    )

    def goASLTT(e):
        page.go("/ASLTT")
        page.overlay.append(audio1)
        img_view.src = "icon.png"

    def route_change(route):
        page.views.clear()
        page.views.append(

            ft.View(
                "/",
                appbar=ft.AppBar(title=ft.Text("UpLink: Communication made simple")),
                padding = 20,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                vertical_alignment=ft.MainAxisAlignment.CENTER,
                
                controls=[
                    ft.Row(
                        [
                            ft.ElevatedButton(content=ft.Text("ASLTS", weight=ft.FontWeight.BOLD, size=80), on_click=goASLTT, width=350, height=200, bgcolor="blue"),       
                    ],
                    expand=1,
                    alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Row(             
                        [
                        ft.ElevatedButton(content=ft.Text("STT", weight=ft.FontWeight.BOLD, size=80), on_click=lambda _: page.go("/STT"), width=350, height=200, bgcolor="blue")
                    ],
                    expand=1,
                    alignment=ft.MainAxisAlignment.CENTER,
                    ), 
                ]
            ),

            

        )
        if page.route == "/ASLTT":
            # Reset the image source and clear the base64 image
            img_view.src_base64 = None  # Clear the base64 image
            img_view.src = "icon.png"   # Reset to the default icon
            page.views.append(
                ft.View(
                    "/ASLTT",

                    [
                        ft.AppBar(title=ft.Text("American Sign Language-To-Text"), bgcolor=ft.Colors.BLACK),
                        safe_space,
                        
                        ],
                )
            )

        elif page.route == "/STT":
            page.views.append(
                ft.View(
                    "/STT",
                    [

                        ft.AppBar(title=ft.Text("Speech-To-Text"), bgcolor=ft.Colors.BLACK),
                        STTsafe_space,

                        ],
                )
            )    

        page.update()

    def view_pop(view):
        global cap
        if cap is not None and cap.isOpened():
            cap.release()

        page.overlay.clear()

        img_view.src_base64 = None  
        img_view.src = "icon.png"
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)


    async def button_play(e):
        await play()

    async def button_stop(e):
        uiPrint("stop button pressed")
        page.update()
        await stop()

    async def play():
        # Set up the video capture (using webcam in this case)
        global cap, recognizer

        cap = cv2.VideoCapture(0)  # 0 for the default webcam
        if not cap.isOpened():
            uiPrint("Error: Could not open video stream.")
            exit()

        # Check if the model exists
        model_path = os.path.join(os.path.dirname(__file__), 'als.task')
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")

        # Create a GestureRecognizer object
        recognizer = vision.GestureRecognizer.create_from_model_path(model_path)

        await display_img(True)

    async def process_frame(frame):

        global recognizer

        """
        Process each frame for gesture recognition.
        """
        # Convert the frame to the format required by MediaPipe (MP Image)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)

        # Run gesture recognition
        recognition_result = recognizer.recognize(mp_image)
        
        # Check if gestures are recognized
        if recognition_result.gestures and recognition_result.gestures[0]:
            top_gesture = recognition_result.gestures[0][0]
            # Display the gesture name and score
            gesture_text = f"Gesture: {top_gesture.category_name} ({top_gesture.score:.2f})"
            print(gesture_text)
            cv2.putText(frame, gesture_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            print(top_gesture.category_name)
            await a_final(top_gesture.category_name)
        else:
            cv2.putText(frame, "No gesture recognized", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        return frame

    async def display_img(state=bool):

        if state and cap is not None and cap.isOpened():
            ret, frame = cap.read()

            if ret:
                
                processed_frame = await process_frame(frame)

                # Convert frame to JPEG
                base64_data = frame_to_base64(processed_frame)

                await asyncio.sleep(0.2)

                img_view.src_base64 = base64_data
                page.update()

                await asyncio.sleep(0)

                await display_img(True)

            else: 

                await display_img(False)

        else:

            if cap is not None:
                cap.release()

            img_view.src_base64 = None

            img_view.src = "icon.png"

            uiPrint("feed stopped")

            page.update()

            await asyncio.sleep(0)
    
    def frame_to_base64(frame: np.ndarray) -> str:
        # Convert the frame (NumPy array) to JPEG format
        _, buffer = cv2.imencode('.jpg', frame)  # You can also use '.png' for PNG format
        byte_data = buffer.tobytes()
        
        # Encode the byte data to base64
        base64_str = base64.b64encode(byte_data).decode('utf-8')
        return base64_str
    
    async def stop():
        global cap
        if cap is not None and cap.isOpened():
            cap.release()
            cap = None

        page.update()
        uiPrint("Camera feed stopped and image reset.")

    def uiPrint(text=""):
        print(text)
        err_log.value = text
        err_log.update()

    def stt_uiPrint(text=""):
        print(text)
        STTerr_log.value = text
        STTerr_log.update()

    img_view = ft.Image(height=220)

    start_button = ft.ElevatedButton(text="Start", expand=True, on_click=button_play)

    stop_button = ft.ElevatedButton(text="End", expand=True, on_click=button_stop)

    generated_text = ft.Text("Generated text will be displayed here", expand=True)

    err_log = ft.Text("Error messages will be displayed here", expand=True, color="blue")
    
    testTF = ft.TextField(on_submit=add_tts)
        
    #tts_button = ft.ElevatedButton("Stop playing", on_click=lambda _: audio1.pause())

    button_row = ft.Row(alignment=ft.MainAxisAlignment.SPACE_EVENLY, expand=True, controls=[start_button, stop_button])
    main_col = ft.Column(alignment=ft.MainAxisAlignment.START, expand=True, 
                        controls=[ft.Row(controls=[img_view], alignment=ft.MainAxisAlignment.CENTER), generated_text, button_row, err_log, testTF,])

    safe_space = ft.SafeArea(main_col)

    async def STTstart_pressed(e):
        global STTstate
        STTstate = True
        await STT_play()

    async def STTstop_pressed(e):
        await STT_stop()

    async def STT_stop():
        global STTstate
        STTstate = False

    async def STT_play():
        recognizer = sr.Recognizer()
        mic = sr.Microphone()

        with mic as source:
            stt_uiPrint("Adjusting for ambient noise... Please wait.")
            recognizer.adjust_for_ambient_noise(source)

            while STTstate:
                try:
                    print("Listening...")
                    # Capture audio from the microphone within the 'with' statement
                    audio = recognizer.listen(source)
 
                    print("Recognizing...")
                    # Recognize speech using PocketSphinx in a separate thread
                    text = await asyncio.to_thread(recognizer.recognize_sphinx, audio)
                    stt_uiPrint(f"Recognized: {text}")

                except sr.UnknownValueError:
                    stt_uiPrint("Sorry, I couldn't understand the audio.")
                except sr.RequestError as e:
                    stt_uiPrint(f"Error with the PocketSphinx service: {e}")
                except Exception as e:
                    stt_uiPrint(f"An error occurred: {e}")

            stt_uiPrint("stt has been stopped")
        
    STTstart_button = ft.ElevatedButton(text="Start", expand=True, on_click=STTstart_pressed)

    STTstop_button = ft.ElevatedButton(text="End", expand=True, on_click=STTstop_pressed)

    STTgenerated_text = ft.Text("Generated text will be displayed here", expand=True)

    STTerr_log = ft.Text("Error messages will be displayed here", expand=True, color="blue")

    STTbutton_row = ft.Row(alignment=ft.MainAxisAlignment.SPACE_EVENLY, expand=True, controls=[STTstart_button, STTstop_button])
    STTmain_col = ft.Column(alignment=ft.MainAxisAlignment.START, expand=True, 
                        controls=[STTgenerated_text, STTbutton_row, STTerr_log])

    STTsafe_space = ft.SafeArea(STTmain_col)



ft.app(main, assets_dir="assets")

