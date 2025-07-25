import os
import sys
import contextlib
import atexit
import speech_recognition as sr
import pyttsx3
import webbrowser
import datetime
import cv2
import pywhatkit
import wikipedia
import psutil
from llama_cpp import Llama


# Optional: Redirect stderr to null (for C-level logs)
sys.stderr = open(os.devnull, 'w')

# Register LLaMA cleanup
@atexit.register
def cleanup_llama():
    try:
        llm.close()
        import types
        llm.__del__ = types.MethodType(lambda self: None, llm)
    except:
        pass  # Swallow any errors on exit

# Initialize TTS engine
engine = pyttsx3.init()
#  Set Microsoft Zira as the default voice
engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0')
engine.setProperty('rate', 170)   # Adjust speech speed (optional)
engine.setProperty('volume', 1.0) # Max volume (optional)


# Context manager to suppress stderr (for llama.cpp noise)
@contextlib.contextmanager
def suppress_stderr():
    with open(os.devnull, 'w') as fnull:
        original_stderr = sys.stderr
        sys.stderr = fnull
        try:
            yield
        finally:
            sys.stderr = original_stderr

#  Wrap only model loading
with suppress_stderr():
    llm = Llama(model_path="C:/Users/ayush/models/mistral-7b.gguf", n_ctx=2048)

# Core Functions
def chat_local(prompt):
    if not prompt.strip():
        return ""  #  Skip processing empty prompt

    print(f"User: {prompt}")
    output = llm(
        f"[INST] {prompt} [/INST]",
        max_tokens=256,
        stop=["</s>"]
    )
    response = output["choices"][0]["text"].strip()
    print(f"Jarvis: {response}")
    return response

def say(text):
    engine.say(text)
    engine.runAndWait()

def log_interaction(user_input, response):
    if user_input.strip() == "":
        return  # Don't log empty input
    with open("jarvis_log.txt", "a", encoding="utf-8") as f:
        f.write(f"User: {user_input}\nJarvis: {response}\n\n")

def emotional_chat(prompt):
    lower_prompt = prompt.lower()

    if "sad" in lower_prompt or "feeling low" in lower_prompt or "depressed" in lower_prompt:
        say("I'm really sorry you're feeling this way. You're not alone. Would you like to hear a joke or talk more?")
        return

    if "tell me a joke" in lower_prompt:
        say("Here's a joke for you.")
        prompt = "Tell me a funny joke."

    elif "i am bored" in lower_prompt or "i'm bored" in lower_prompt:
        say("Let's do something fun. I can tell you a fact, a joke, or play music.")

    reply = chat_local(prompt)
    if reply:
        log_interaction(prompt, reply)
        say(reply)

def close_browser():
    browsers = ["chrome.exe", "msedge.exe", "firefox.exe"]
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in browsers:
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def takeCommand():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.pause_threshold = 1
        try:
            audio = r.listen(source)
            query = r.recognize_google(audio, language='en-in')
            print(f"User said: {query}")
            return query
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            say("Network issue, please check your connection.")
            return ""

def open_camera():
    import tkinter as tk
    from PIL import Image, ImageTk
    import threading
    import speech_recognition as sr

    say("Opening camera. Say 'close camera' to stop")

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    root = tk.Tk()
    root.title("Jarvis Camera")
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)

    lmain = tk.Label(root)
    lmain.pack()

    stop_camera = False

    def close_cam():
        nonlocal stop_camera
        stop_camera = True
        say("Camera closed")
        cap.release()
        root.destroy()

    def show_frame():
        if stop_camera:
            return
        ret, frame = cap.read()
        if ret:
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            lmain.imgtk = imgtk
            lmain.configure(image=imgtk)
        lmain.after(10, show_frame)

    #  Background thread to listen for "close camera"
    def listen_for_close():
        r = sr.Recognizer()
        while not stop_camera:
            try:
                with sr.Microphone() as source:
                    r.adjust_for_ambient_noise(source, duration=0.5)
                    print(" Listening inside camera window...")
                    audio = r.listen(source, timeout=5, phrase_time_limit=6)
                    command = r.recognize_google(audio, language='en-in').lower()
                    print("You said (in camera):", command)
                    if "close camera" in command:
                        root.after(0, close_cam)  # safely call from thread
                        break
            except:
                pass

    threading.Thread(target=listen_for_close, daemon=True).start()

    root.protocol("WM_DELETE_WINDOW", close_cam)
    tk.Button(root, text="Close Camera", command=close_cam).pack()

    show_frame()
    root.mainloop()




# ------------------ MAIN LOOP ------------------

if __name__ == '__main__':
    print("Jarvis A.I Starting...")
    say("Hello, I am Jarvis")

    while True:
        print("Listening...")
        query = takeCommand().lower()
        if not query.strip():
            continue

        if "bye" in query or "tata" in query or "see you later" in query:
            say("Goodbye! Have a great day.")
            print("Jarvis shutting down...")
            break

        sites = [
            ["youtube", "https://www.youtube.com"],
            ["wikipedia", "https://www.wikipedia.com"],
            ["google", "https://www.google.com"]
        ]
        for site in sites:
            if f"open {site[0]}" in query:
                say(f"Opening {site[0]} sir...")
                webbrowser.open(site[1])
            if "close it" in query:
                close_browser()

        if "play" in query:
            song = query.replace("play", "").strip()
            say(f"Playing {song}")
            pywhatkit.playonyt(song)

        if "stop music" in query:
            say("Stopping the music")
            close_browser()

        if "the time" in query:
            strfTime = datetime.datetime.now().strftime("%H:%M:%S")
            say(f"Sir the time is {strfTime}")

        if "open camera" in query:
            open_camera()

        if "date" in query:
            today = datetime.date.today()
            say(f"Sir the date is {today.day}/{today.month}/{today.year}")

        if "who is" in query:
            person = query.replace("who is", "")
            try:
                info = wikipedia.summary(person, 1)
                say(info)
            except:
                say("Sorry,I couldn't find that information.Let me search it in on Google.")
                webbrowser.open("https://www.google.com/search?q=" + person)

        if "what is" in query:
            topic = query.replace("what is", "")
            try:
                info = wikipedia.summary(topic, 1)
                say(info)
            except:
                say("Sorry,I couldn't find that information.Let me search it in on Google.")
                webbrowser.open("https://www.google.com/search?q=" + topic)

        if "how" in query:
            topic = query.replace("how", "")
            try:
                info = wikipedia.summary(topic, 1)
                say(info)
            except:
                say("Sorry,I couldn't find that information.Let me search it in on Google.")
                webbrowser.open("https://www.google.com/search?q=" + topic)

        if "define" in query:
            topic = query.replace("define", "")
            try:
                info = wikipedia.summary(topic, 1)
                say(info)
            except:
                say("Sorry,I couldn't find that information.Let me search it in on Google.")
                webbrowser.open("https://www.google.com/search?q=" + topic)

        if "explain" in query:
            topic = query.replace("explain", "")
            try:
                info = wikipedia.summary(topic, 1)
                say(info)
            except:
                say("Sorry,I couldn't find that information.Let me search it in on Google.")
                webbrowser.open("https://www.google.com/search?q=" + topic)

        if "chat" in query or "talk" in query:
            say("Chat mode activated. Say 'exit chat' to leave.")
            while True:
                follow_up = takeCommand().lower()
                if "exit chat" in follow_up or "stop" in follow_up:
                    say("Exiting chat mode.")
                    break
                emotional_chat(follow_up)

        if "weather" in query:
            say("Searching the weather forecast...")
            webbrowser.open("https://www.google.com/search?q=weather+today")

        if "set a timer for" in query:
            import time
            import re
            mins = re.findall(r'\d+', query)
            if mins:
                seconds = int(mins[0]) * 60
                say(f"Setting a timer for {mins[0]} minutes")
                time.sleep(seconds)
                say("Time's up!")

        if "screenshot" in query:
            try:
                import pyautogui
                save_path = os.path.join(os.getcwd(), "screenshot.png")
                image = pyautogui.screenshot()
                image.save(save_path)
                say(f"Screenshot saved")
                print(f"Screenshot saved at {save_path}")
            except Exception as e:
                say("Failed to take screenshot.")
                print("Screenshot error:", e)




























