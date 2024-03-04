from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from pydub import AudioSegment
import googletrans
import os
import uuid
from googletrans import Translator
import gtts
from gtts import gTTS
import time
from pydub import AudioSegment
from IPython.display import Audio
import speech_recognition as sr
from PIL import Image
import pytesseract
from PyPDF2 import PdfFileReader
from PyPDF2 import PdfReader
import fitz  # PyMuPDF

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

app = Flask(__name__)
language_codes = googletrans.LANGUAGES
languages = [{"code": code, "name": name} for code, name in language_codes.items()]

@app.route('/')
def index():
    return render_template('index.html',languages=languages)

# Define the directory to store uploaded audio files
UPLOAD_FOLDER = UPLOAD_FOLDER = r'C:\Users\HP\Desktop\final-sts-flask\Text_Translator_Text_To_Speech\static'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
# Define the list of allowed audio file extensions
#ALLOWED_EXTENSIONS = {}

# Function to check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Define the directory to store uploaded documents
UPLOAD_FOLDER = 'static/documents'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Define the list of allowed document file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf','wav','mp3'}

# Function to check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Function to extract text from image using OCR
def extract_text_from_image(image_path):
    return pytesseract.image_to_string(image_path)

# Function to extract text from PDF using PyPDF2
# def extract_text_from_pdf(pdf_path):
#     try:
#         # Open the PDF file using PdfReader
#         with open(pdf_path, "rb") as file:
#             reader = PdfReader(file)
#             num_pages = len(reader.pages)  # Get the number of pages in the PDF

#             # Iterate through each page and extract text
#             text = ""
#             for page_num in range(num_pages):
#                 page = reader.pages[page_num]
#                 text += page.extract_text()

#             return text
#     except Exception as e:
#         return f"Error extracting text from PDF: {str(e)}"

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
                    image_text = extract_text_from_image(image_name)
                    text += image_text + "\n"
                    os.remove(image_name)  # Clean up the temporary image file

    if text.strip():
        translated_text = translate_text(text, target_lang)
        return translated_text
    else:
        return "Text extraction from PDF failed. No text to translate."

def translate_audio_to_text(audio_path):
    recognizer = sr.Recognizer()
    audio_file = sr.AudioFile(audio_path)

    with audio_file as source:
        audio_data = recognizer.record(source)
    
    try:
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        return "Speech Recognition could not understand audio"
    except sr.RequestError as e:
        return f"Could not request results from Speech Recognition service; {e}"

def translate_text(text, target_lang):
    translator = Translator()
    translation = translator.translate(text, dest=target_lang)
    return translation.text

# Function to generate audio from translated text
def generate_audio(text, target_lang):
    audio_filename = f"static/{uuid.uuid4().hex}.mp3"
    tts = gTTS(text, lang=target_lang)
    tts.save(audio_filename)
    return audio_filename

@app.route("/translate_text", methods=["GET", "POST"])
def translatetext():
    if request.method == "POST":
        input_text = request.form.get("input_text")
        target_language = request.form.get("target_language")
        translated_text = translate_text(input_text, target_language)
        timestamp = int(time.time())
        filename = f"static/op_{timestamp}.mp3"  
        tts = gTTS(translated_text, lang=target_language)
        tts.save(filename)  
        return render_template("index.html", languages=languages, input_text=input_text, translated_text=translated_text, audio_filename=filename)
    return render_template("index.html", languages=languages)

@app.route("/translate_voice", methods=["POST"])
def translatevoice():
    target_language = request.form.get("target_language")

    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Speak something...")
        audio_data = recognizer.listen(source)
    
    try:
        recognized_text = recognizer.recognize_google(audio_data)
        translated_text = translate_text(recognized_text, target_language)
        timestamp = int(time.time())
        filename = f"static/op_{timestamp}.mp3"
        tts = gTTS(translated_text, lang=target_language)
        tts.save(filename)
        return render_template("index.html", languages=languages, translated_voice_text=translated_text, audio_filename=filename)
    except sr.UnknownValueError:
        return render_template("index.html", languages=languages, error="Could not understand audio")
    except sr.RequestError as e:
        return render_template("index.html", languages=languages, error=f"Could not request results; {e}")


def convert_to_wav(audio_path):
    # Load the MP3 file
    audio = AudioSegment.from_mp3(audio_path)

    # Create a new filename for the WAV file
    wav_filename = os.path.splitext(audio_path)[0] + ".wav"

    # Export the audio to WAV format
    audio.export(wav_filename, format="wav")
    return wav_filename

@app.route("/translate_audio", methods=["POST"])
def translate_audio():
    target_language = request.form.get("target_language")

    if "audio_file" not in request.files:
        return render_template("index.html", error="No file part")

    audio_file = request.files["audio_file"]

    if audio_file.filename == "":
        return render_template("index.html", error="No selected file")

    if audio_file and allowed_file(audio_file.filename):
        filename = secure_filename(audio_file.filename)
        audio_path = os.path.join(UPLOAD_FOLDER, filename)
        audio_file.save(audio_path)

        # Convert MP3 to WAV if the uploaded file is in MP3 format
        if audio_path.lower().endswith(".mp3"):
            audio_path = convert_to_wav(audio_path)

        translated_text = translate_audio_to_text(audio_path)
        translated_text = translate_text(translated_text, target_language)
        audio_filename = generate_audio(translated_text, target_language)

        return render_template("index.html", languages=languages, translated_audio_text=translated_text,
                               audio_file=audio_filename)
    return render_template("index.html", error="Invalid file format")


# @app.route("/translate_document", methods=["POST"])
# def translate_document():
#     target_language = request.form.get("target_language")

#     if "document_file" not in request.files:
#         return render_template("index.html", error_document="No file part")

#     document_file = request.files["document_file"]

#     if document_file.filename == "":
#         return render_template("index.html", error_document="No selected file")

#     if document_file and allowed_file(document_file.filename):
#         filename = secure_filename(document_file.filename)
#         document_path = os.path.join(UPLOAD_FOLDER, filename)
#         document_file.save(document_path)

#         # Extract text from document based on file type
#         if filename.endswith(('.png', '.jpg', '.jpeg')):
#             extracted_text = extract_text_from_image(document_path)
#         elif filename.endswith('.pdf'):
#             extracted_text = extract_text_from_pdf(document_path)

#         # Translate extracted text
#         translated_text = translate_text(extracted_text, target_language)
#         audio_filename = generate_audio(translated_text, target_language)

#         return render_template("index.html", translated_document_text=translated_text,
#                                audio_filename_document=audio_filename)

#     return render_template("index.html", error_document="Invalid file format")

@app.route("/translate_document", methods=["POST"])
def translate_document():
    target_language = request.form.get("target_language")

    if "document_file" not in request.files:
        return render_template("index.html", error_document="No file part")

    file = request.files["document_file"]

    if file.filename == "":
        return render_template("index.html", error_document="No selected file")

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Process PDF or image file based on its type
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            translated_text = extract_text_from_image(file_path)
        elif filename.endswith('.pdf'):
            translated_text = process_pdf_file(file_path, target_language)
        else:
            return render_template("index.html", error_document="Unsupported file format")

        # Translate extracted text and generate audio
        audio_filename = generate_audio(translated_text, target_language)

        return render_template("index.html", languages=languages, translated_document_text=translated_text,
                               audio_filename_document=audio_filename)

    return render_template("index.html", error_document="Invalid file format")


if __name__ == "__main__":
    app.run(debug=True)

# @app.route("/translate_audio", methods=["POST"])
# def translate_audio():
#     target_language = request.form.get("target_language")

#     if "audio_file" not in request.files:
#         return render_template("index.html", error="No file part")

#     audio_file = request.files["audio_file"]

#     if audio_file.filename == "":
#         return render_template("index.html", error="No selected file")

#     if audio_file and allowed_file(audio_file.filename):
#         filename = secure_filename(audio_file.filename)
#         audio_path = os.path.join(UPLOAD_FOLDER, filename)
#         audio_file.save(audio_path)

#         translated_text = translate_audio_to_text(audio_path)
#         translated_text = translate_text(translated_text, target_language)
#         audio_filename = generate_audio(translated_text, target_language)

#         return render_template("index.html", translated_audio_text=translated_text,
#                                audio_file=audio_filename)

#     return render_template("index.html", error="Invalid file format")















# app.py

# from flask import Flask, render_template, request, make_response
# from werkzeug.utils import secure_filename
# from googletrans import Translator
# import os
# import uuid
# import time
# import speech_recognition as sr
# from gtts import gTTS

# app = Flask(__name__)
# language_codes = googletrans.LANGUAGES
# languages = [{"code": code, "name": name} for code, name in language_codes.items()]

# @app.route('/')
# def index():
#      return render_template('index.html',languages=languages)

# translator = Translator()

# UPLOAD_FOLDER = 'static'
# if not os.path.exists(UPLOAD_FOLDER):
#     os.makedirs(UPLOAD_FOLDER)

# ALLOWED_EXTENSIONS = {'wav', 'mp3'}

# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# def translate_text(text, target_lang):
#     translation = translator.translate(text, dest=target_lang)
#     return translation.text

# def generate_audio(text, target_lang):
#     audio_filename = f"{uuid.uuid4().hex}.mp3"
#     tts = gTTS(text, lang=target_lang)
#     tts.save(os.path.join(UPLOAD_FOLDER, audio_filename))
#     return audio_filename

# def translate_audio_to_text(audio_path):
#     recognizer = sr.Recognizer()
#     audio_file = sr.AudioFile(audio_path)

#     with audio_file as source:
#         audio_data = recognizer.record(source)
    
#     try:
#         text = recognizer.recognize_google(audio_data)
#         return text
#     except sr.UnknownValueError:
#         return "Speech Recognition could not understand audio"
#     except sr.RequestError as e:
#         return f"Could not request results from Speech Recognition service; {e}"

# # @app.route('/')
# # def index():
# #     return render_template('index.html', languages=['en', 'fr', 'es'])

# @app.route("/translate_text", methods=["POST"])
# def translate_text_route():
#     if request.method == "POST":
#         input_text = request.form.get("input_text")
#         target_language = request.form.get("target_language")
#         translated_text = translate_text(input_text, target_language)
#         audio_filename = generate_audio(translated_text, target_language)
#         return render_template("index.html", input_text=input_text, 
#                                translated_text=translated_text, audio_filename=audio_filename)
#     return render_template("index.html")

# @app.route("/translate_voice", methods=["POST"])
# def translate_voice():
#     target_language = request.form.get("target_language")

#     recognizer = sr.Recognizer()
#     with sr.Microphone() as source:
#         print("Speak something...")
#         audio_data = recognizer.listen(source)
    
#     try:
#         recognized_text = recognizer.recognize_google(audio_data)
#         translated_text = translate_text(recognized_text, target_language)
#         audio_filename = generate_audio(translated_text, target_language)
#         return render_template("index.html", translated_voice_text=translated_text, 
#                                audio_filename=audio_filename)
#     except sr.UnknownValueError:
#         return render_template("index.html", error="Could not understand audio")
#     except sr.RequestError as e:
#         return render_template("index.html", error=f"Could not request results; {e}")

# @app.route("/translate_audio", methods=["POST","GET"])
# def translate_audio():
#     target_language = request.form.get("target_language")

#     if "audio_file" not in request.files:
#         return render_template("index.html", error="No file part")

#     audio_file = request.files["audio_file"]

#     if audio_file.filename == "":
#         return render_template("index.html", error="No selected file")

#     if audio_file and allowed_file(audio_file.filename):
#         filename = secure_filename(audio_file.filename)
#         audio_path = os.path.join(UPLOAD_FOLDER, filename)
#         audio_file.save(audio_path)

#         translated_text = translate_audio_to_text(audio_path)
#         translated_text = translate_text(translated_text, target_language)
#         audio_filename = generate_audio(translated_text, target_language)

#         return render_template("index.html", translated_audio_text=translated_text,
#                                audio_filename=audio_filename)

#     return render_template("index.html", error="Invalid file format")

# if __name__ == "__main__":
#     app.run(debug=True)

