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
import socket  # Import socket for checking internet connection
import flet_audio as fta

cap = None
ASLTSstate = False
STTstate = False
sttRecognizer = sr.Recognizer()
mic = sr.Microphone()
audioState = False

aslFilename = 'bright.task'

# Check if the model exists
model_path = os.path.join(os.path.dirname(__file__), aslFilename)

# Create a GestureRecognizer object
asltsRecognizer = vision.GestureRecognizer.create_from_model_path(model_path)

def isConnected():

    global audioState

    try:
        # Try to connect to a well-known host
        socket.create_connection(("www.google.com", 80))
        audioState = True
    except OSError:
        audioState = False

async def main(page: ft.Page):

    page.adaptive = True

    page.title = "UpLink"

    isConnected()

    # Check for internet connection
    if not audioState:
        print("No internet connection. Please check your Wi-Fi.")

    else: 

        print("wifi")

        data = io.BytesIO()

        # create a gTTS object
        gtts = gTTS(text="test", lang="en", slow=False)

        gtts.write_to_fp(data)

        data.seek(0)

        speech = base64.b64encode(data.read()).decode('utf-8')

        transcribedSpeechPlayer = fta.Audio(
            src_base64=speech
        )

    async def updateAudio(asl = ""):

        transcribedSpeechPlayer.release()

        data = io.BytesIO()

        # create a gTTS object
        try: gtts = gTTS(text=asl, lang="en", slow=False)
        except AssertionError: gtts = gTTS(text="space", lang="en", slow=False)

        gtts.write_to_fp(data)

        data.seek(0)

        speech = base64.b64encode(data.read()).decode('utf-8')

        transcribedSpeechPlayer.src_base64 = speech

        transcribedSpeechPlayer.update()
        transcribedSpeechPlayer.play()

        await asyncio.sleep(3)

        print(f"Generated audio for text: {asl}")


    def goASLTT(e):
        page.go("/ASLTT")
        if audioState: page.overlay.append(transcribedSpeechPlayer)
        img_view.src = "icon.png"

    #Callback for starting the ASLTS
    async def initializeASLTS(e):
        await play()

    #Callback for stopping ASLTS
    async def releaseASLTS(e):
        await stop()

    async def play():
        global cap

        print("attempting to start aslts")

        #transcribedSpeechPlayer.play()
        #await asyncio.sleep(5)

        # Set up the video capture
        cap = cv2.VideoCapture(0)  

        if not cap.isOpened():
            ASLTSPrint("Error: Could not open video stream.")
            return  # Change exit() to return to handle the error gracefully


        await display_img()

    async def display_img():

        global cap

        if cap is not None and cap.isOpened():

            ret, frame = cap.read()
            print(ret)
            
            while cap is not None:
                
                ret, frame = cap.read()
                processed_frame = await process_frame(frame)

                # Convert frame to JPEG
                base64_data = frame_to_base64(processed_frame)

                img_view.src = None
                img_view.src_base64 = base64_data
                page.update()

                await asyncio.sleep(0.2)

        img_view.src_base64 = None

        img_view.src = "icon.png"

        ASLTSPrint("feed stopped")

        page.update()

        await asyncio.sleep(2)


    async def process_frame(frame):
        global audioState

        #Process each frame for gesture recognition.
    
        # Convert the frame to the format required by MediaPipe (MP Image)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)

        # Run gesture recognition
        recognition_result = asltsRecognizer.recognize(mp_image)
        
        # Check if gestures are recognized
        if recognition_result.gestures and recognition_result.gestures[0]:
            top_gesture = recognition_result.gestures[0][0]
            # Display the gesture name and score
            gesture_text = f"Gesture: {top_gesture.category_name} ({top_gesture.score:.2f})"
            ASLTSPrint(gesture_text)
            cv2.putText(frame, gesture_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            print(top_gesture.category_name)
            if audioState: await updateAudio(f"{top_gesture.category_name}")

        else:
            ASLTSPrint("No gesture recognized")
            cv2.putText(frame, "No gesture recognized", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            await asyncio.sleep(0.2)

        return frame
    
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
        ASLTSPrint("Camera feed stopped and image reset.")
        await asyncio.sleep(1)

    def ASLTSPrint(text=""):
        print(text)
        asltsText.value = text
        asltsText.update()

    def STTPrint(text=""):
        print(text)
        sttText.value = text
        sttText.update()

    img_view = ft.Image(height=400)

    asltsStartButton = ft.ElevatedButton(content=ft.Text(value="Start", size=40), expand=True, on_click= initializeASLTS, height=80)

    asltsStopButton = ft.ElevatedButton(content=ft.Text(value="End", size=40), expand=True, on_click= releaseASLTS, height=80)

    asltsText = ft.Text("Generated text will be displayed here", expand=True, size=40)

    button_row = ft.Row(alignment=ft.MainAxisAlignment.SPACE_EVENLY, expand=True, controls=[asltsStartButton, asltsStopButton])
    
    main_col = ft.Column(
        alignment=ft.MainAxisAlignment.START, 
        expand=True, 
        controls=[
            ft.Row(controls=[img_view], 
                   alignment=ft.MainAxisAlignment.CENTER), 
                   asltsText, 
                   button_row, 
                   ])

    safe_space = ft.SafeArea(main_col)  # Define safe_space before it is used

    # this is called from the background thread
    def callback(recognizer, audio):
        try:
            STTPrint("pocketsphinx thinks you said " + recognizer.recognize_sphinx(audio))
        except sr.UnknownValueError:
            STTPrint("pocketsphinx could not understand audio")
        except Exception as e:
            STTPrint(f"An error occurred: {e}")
        

    async def initializeSTT(e):
        await startSTT()

    async def releaseSTT(e):
        listener(wait_for_stop=False)
        STTPrint("stopped listening")
    
    async def startSTT():

        global STTstate, sttRecognizer, listener

        with mic as source:
            STTPrint("Adjusting for ambient noise... Please wait.")
            sttRecognizer.adjust_for_ambient_noise(source)

        listener = sttRecognizer.listen_in_background(source, callback)
        
    
    sttStartButton = ft.ElevatedButton(content=ft.Text(value="Start", size=40), expand=True, on_click=initializeSTT, height=80)

    sttStopButton = ft.ElevatedButton(content=ft.Text(value="End", size=40), expand=True, on_click=releaseSTT, height=80)

    sttText = ft.Text("Generated text will be displayed here", size=40, height=80)

    STTbutton_row = ft.Row(alignment=ft.MainAxisAlignment.SPACE_EVENLY, expand=True, controls=[sttStartButton, sttStopButton])
    STTmain_col = ft.Column(alignment=ft.MainAxisAlignment.START, expand=True, 
                        controls=[sttText, STTbutton_row], spacing=40)

    STTsafe_space = ft.SafeArea(STTmain_col)

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
                            ft.ElevatedButton(content=ft.Text("ASLTS", weight=ft.FontWeight.BOLD, size=80), on_click=goASLTT, width=350, height=200),       
                    ],
                    expand=1,
                    alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Row(             
                        [
                        ft.ElevatedButton(content=ft.Text("STT", weight=ft.FontWeight.BOLD, size=80), on_click=lambda _: page.go("/STT"), width=350, height=200)
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
                        safe_space,  # Use safe_space after it has been defined

                        
                        ],
                )
            )

        elif page.route == "/STT":

            page.views.append(
                ft.View(
                    "/STT",
                    [

                        ft.AppBar(title=ft.Text("Speech-To-Text"), bgcolor=ft.Colors.BLACK),
                        STTsafe_space,  # Use STTsafe_space after it has been defined


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



ft.app(main, assets_dir="assets")
