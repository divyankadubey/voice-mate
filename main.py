import pyttsx3
import pyperclip
import pytesseract
from PIL import Image
from langdetect import detect
from PIL import ImageGrab
import pygetwindow as gw
from gtts import gTTS
import tkinter as tk
from tkinter import filedialog, messagebox
import speech_recognition as sr
import logging
import os
import time

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Initialize Text-to-Speech Engine
engine = pyttsx3.init()

# Configure Logger
LOG_FILE = "screen_reader.log"
logging.basicConfig(filename=LOG_FILE, level=logging.ERROR, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Configure TTS Engine
def configure_tts_engine():
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate - 50)
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)  # Default to first voice

# Update TTS Settings (via GUI customization)
def update_tts_settings(rate, voice_index):
    try:
        engine.setProperty('rate', rate)
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[voice_index].id)
    except Exception as e:
        logging.error(f"Failed to update TTS settings: {e}")
        messagebox.showerror("Error", f"Failed to update settings: {e}")

configure_tts_engine()

# Function to capture and read text from the active window
def read_active_window_text():
    try:
        time.sleep(1)
        # Get the active window
        active_window = gw.getActiveWindow()
        if active_window:
            print(f"Active Window Title: {active_window.title}")

            # Capture the active window's region
            left, top, right, bottom = active_window.left, active_window.top, active_window.right, active_window.bottom
            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))

            # Perform OCR on the screenshot
           
            text = pytesseract.image_to_string(screenshot)

            # Check if text was detected
            if text.strip():
                print(f"Extracted Text: {text}")
                engine.say(text)
                engine.runAndWait()
            else:
                print("No readable text found in the active window.")
        else:
            print("No active window detected.")
    except Exception as e:
        print(f"Error reading text from active window: {e}")


# Read Text from Clipboard
def read_clipboard_text():
    try:
        text = pyperclip.paste()
        if text:
            language = detect(text)
            print(f"Detected language: {language}")
            voices = engine.getProperty('voices')
            if language == 'en':
                engine.setProperty('voice', voices[0].id)
            elif language == 'es':
                engine.setProperty('voice', voices[1].id)
            engine.say(text)
            engine.runAndWait()
        else:
            messagebox.showinfo("Info", "No text found on the clipboard to read!")
    except Exception as e:
        logging.error(f"Error reading clipboard text: {e}")
        messagebox.showerror("Error", f"Failed to read clipboard text: {e}")

# Read Text from Image
def read_text_from_image(image_path=None):
    try:
        if not image_path:
            image_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if image_path:
            text = pytesseract.image_to_string(Image.open(image_path))
            if text.strip():
                engine.say(text)
                engine.runAndWait()
            else:
                messagebox.showinfo("Info", "No readable text found in the image!")
        else:
            messagebox.showinfo("Info", "No image selected!")
    except Exception as e:
        logging.error(f"Error reading text from image: {e}")
        messagebox.showerror("Error", f"Failed to read text from image: {e}")

# Save Clipboard Text to Audio
def save_clipboard_to_audio():
    try:
        text = pyperclip.paste()
        if text:
            tts = gTTS(text=text, lang=detect(text))
            save_path = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("Audio Files", "*.mp3")])
            if save_path:
                tts.save(save_path)
                messagebox.showinfo("Success", f"Audio saved as {save_path}")
                if not save_path:
                  messagebox.showinfo("Info", "Save operation canceled!")
                  return
        else:
            messagebox.showinfo("Info", "No text found on the clipboard to save!")
    except Exception as e:
        logging.error(f"Error saving clipboard text to audio: {e}")
        messagebox.showerror("Error", f"Failed to save audio: {e}")

# Listen for Voice Commands
def listen_and_execute():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            messagebox.showinfo("Voice Command", "Listening for commands...")
            audio = recognizer.listen(source)
            command = recognizer.recognize_google(audio).lower()
            print(f"Voice Command: {command}")
            if "read clipboard" in command:
                read_clipboard_text()
            elif "read image" in command:
                read_text_from_image()
            elif "save audio" in command:
                save_clipboard_to_audio()
            elif "exit" in command:
                engine.say("Exiting the application. Goodbye!")
                engine.runAndWait()
                exit()
        except Exception as e:
            logging.error(f"Error with voice commands: {e}")
            messagebox.showerror("Error", f"Voice command failed: {e}")

# GUI for Customization and Features
def create_gui():
    root = tk.Tk()
    root.title("Voice Mate")
    
    # Voice Settings
    settings_frame = tk.Frame(root)
    settings_frame.pack(pady=10)

    tk.Label(settings_frame, text="Speech Rate:").grid(row=0, column=0)
    rate_var = tk.IntVar(value=150)
    rate_slider = tk.Scale(settings_frame, from_=50, to=300, orient="horizontal", variable=rate_var)
    rate_slider.grid(row=0, column=1)

    tk.Label(settings_frame, text="Voice:").grid(row=1, column=0)
    voice_var = tk.IntVar(value=0)
    voice_dropdown = tk.OptionMenu(settings_frame, voice_var, *[f"Voice {i}" for i in range(len(engine.getProperty('voices')))])
    voice_dropdown.grid(row=1, column=1)

    def apply_settings():
        update_tts_settings(rate_var.get(), voice_var.get())
        messagebox.showinfo("Success", "Settings updated!")

    apply_button = tk.Button(settings_frame, text="Apply Settings", command=apply_settings)
    apply_button.grid(row=2, column=0, columnspan=2, pady=10)

    # Feature Buttons
    feature_frame = tk.Frame(root)
    feature_frame.pack(pady=20)

    tk.Button(feature_frame, text="Read Active Window", command=read_active_window_text,font=("Arial", 12), bg="blue", fg="white", width=30).pack(pady=5)
    tk.Button(feature_frame, text="Read Clipboard Text", command=read_clipboard_text,font=("Arial", 12), bg="blue", fg="white", width=30).pack(pady=5)
    tk.Button(feature_frame, text="Read Text from Image", command=read_text_from_image,font=("Arial", 12), bg="blue", fg="white", width=30).pack(pady=5)
    tk.Button(feature_frame, text="Save Clipboard Text to Audio", command=save_clipboard_to_audio,font=("Arial", 12), bg="blue", fg="white", width=30).pack(pady=5)
    tk.Button(feature_frame, text="Voice Command Mode", command=listen_and_execute,font=("Arial", 12), bg="blue", fg="white", width=30).pack(pady=5)
    tk.Button(feature_frame, text="Exit", command=root.quit,font=("Arial", 12), bg="blue", fg="white", width=30).pack(pady=5)

    
    
    root.mainloop()

# Main
if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, 'w').close()  
    create_gui()
