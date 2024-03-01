#!/usr/bin/env python
# coding: utf-8
import os
import speech_recognition as sr
from gtts import gTTS
from googletrans import Translator
from pydub import AudioSegment
from PIL import Image
import pytesseract
from PyPDF2 import PdfReader
import fitz  # PyMuPDF


# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# A dictionary containing all the language codes
language_codes = {
    'kannada': 'kn', 'english': 'en', 'hindi': 'hi', 'marathi': 'mr', 'nepali': 'ne'
    # Add more language codes here
}


# Function to capture voice input through microphone
def capture_voice():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        audio = r.listen(source)
    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language='en-in')
        print(f"You said: {query}\n")
        return query
    except Exception as e:
        print("Please say that again...")
        return None


# Function to get source language
def get_source_language():
    print("Please enter your source language:")
    for lang in language_codes:
        print(lang)
    source_lang = input("Source Language: ").lower()
    while source_lang not in language_codes:
        print("Invalid language. Please enter a valid language.")
        source_lang = input("Source Language: ").lower()
    return language_codes[source_lang]


# Function to get target language
def get_target_language():
    print("Please enter your target language:")
    for lang in language_codes:
        print(lang)
    target_lang = input("Target Language: ").lower()
    while target_lang not in language_codes:
        print("Invalid language. Please enter a valid language.")
        target_lang = input("Target Language: ").lower()
    return language_codes[target_lang]


# Function to translate text
def translate_text(text, target_lang):
    translator = Translator()
    translation = translator.translate(text, dest=target_lang)
    return translation.text


# Function to generate and play translated audio
def play_translated_audio(text, target_lang):
    speak = gTTS(text=text, lang=target_lang, slow=False)
    speak.save('translated_audio.mp3')
    os.system('start translated_audio.mp3')


# Function to process uploaded audio file
def process_audio_file(file_path, target_lang):
    r = sr.Recognizer()
    if file_path.lower().endswith('.mp3'):
        audio = AudioSegment.from_mp3(file_path)
    elif file_path.lower().endswith('.wav'):
        audio = AudioSegment.from_wav(file_path)
    else:
        print("Unsupported file format. Please use MP3 or WAV.")
        return
    temp_file = "temp_audio.wav"
    audio.export(temp_file, format="wav")
    with sr.AudioFile(temp_file) as source:
        audio_data = r.record(source)
        try:
            recognized_text = r.recognize_google(audio_data)
            translated_text = translate_text(recognized_text, target_lang)
            print("Translated Text:")
            print(translated_text)
            play_translated_audio(translated_text, target_lang)
        except Exception as e:
            print("Could not recognize the audio. Please try again.", e)


# Function to process image file using OCR
def process_image_file(image_path, target_lang):
    with Image.open(image_path) as img:
        text = pytesseract.image_to_string(img)
        translated_text = translate_text(text, target_lang)
        print("Translated Text from Image:")
        print(translated_text)
        play_translated_audio(translated_text, target_lang)


import os
from PyPDF2 import PdfReader
import fitz

def process_pdf_file(pdf_path, target_lang):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            if page.get_text():
                text += page.get_text()
            else:
                image_list = page.get_images(full=True)
                for image_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    image_name = f"page_{page_num}_image_{image_index}.{image_ext}"
                    with open(image_name, "wb") as image_file:
                        image_file.write(image_bytes)
                    image_text = perform_ocr_on_image(image_name)
                    text += image_text + "\n"
                    os.remove(image_name)  # Clean up the temporary image file

    if text.strip():
        translated_text = translate_text(text, target_lang)
        print("Translated Text from PDF:")
        print(translated_text)
        play_translated_audio(translated_text, target_lang)
    else:
        print("Text extraction from PDF failed. No text to translate.")


# Function to perform OCR on an image
def perform_ocr_on_image(image_path):
    with Image.open(image_path) as img:
        text = pytesseract.image_to_string(img)
    return text


# Main function
def main():
    source_lang = get_source_language()
    target_lang = get_target_language()
    print("How do you want to provide input?")
    print("1. Microphone")
    print("2. Upload Audio File")
    print("3. Upload Image")
    print("4. Upload PDF File")
    print("5. Enter Text")
    choice = input("Enter your choice: ")
    if choice == '1':
        input_text = capture_voice()
        if input_text:
            translated_text = translate_text(input_text, target_lang)
            print("Translated Text:")
            print(translated_text)
            play_translated_audio(translated_text, target_lang)
    elif choice == '2':
        audio_file_path = input("Please provide the full path to the audio file: ")
        if os.path.exists(audio_file_path):
            process_audio_file(audio_file_path, target_lang)
        else:
            print("File not found. Please provide a valid file path.")
    elif choice == '3':
        image_file_path = input("Please provide the full path to the image file: ")
        if os.path.exists(image_file_path):
            process_image_file(image_file_path, target_lang)
        else:
            print("File not found. Please provide a valid file path.")
    elif choice == '4':
        pdf_file_path = input("Please provide the full path to the PDF file: ")
        if os.path.exists(pdf_file_path):
            process_pdf_file(pdf_file_path, target_lang)
        else:
            print("File not found. Please provide a valid file path.")
    elif choice == '5':
        input_text = input("Enter the text you want to translate: ")
        translated_text = translate_text(input_text, target_lang)
        print("Translated Text:")
        print(translated_text)
        play_translated_audio(translated_text, target_lang)
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()







