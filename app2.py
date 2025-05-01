from flask import Flask, render_template, request, redirect, flash, session
from langchain_community.document_loaders import WebBaseLoader
from werkzeug.utils import secure_filename
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os
import fitz  # PyMuPDF
from dotenv import load_dotenv

# Load API key
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
app.secret_key = "secret"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def extract_text(file_path, extension, password=None):
    try:
        if extension == ".pdf":
            with fitz.open(file_path) as doc:
                if doc.needs_pass and not doc.authenticate(password or ""):
                    return None  # PDF is encrypted, wrong or no password
                return "".join([page.get_text() for page in doc])
        return ""
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""

def extract_text_from_url(url):
    try:
        loader = WebBaseLoader(url)
        docs = loader.load()
        return docs[0].page_content if docs else ""
    except Exception as e:
        print(f"URL loading error: {e}")
        return ""

def summarize_text(text):
    try:
        llm = ChatOpenAI(model="gpt-4", temperature=0.5, openai_api_key=openai_api_key)
        trimmed_text = text[:4000]
        messages = [
            SystemMessage(content="You are a helpful assistant that summarizes provided text."),
            HumanMessage(content=f"Summarize this:\n{trimmed_text}")
        ]
        response = llm.invoke(messages)
        return response.content.strip()
    except Exception as e:
        print(f"Summarization error: {e}")
        return "Summary could not be generated."

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        input_type = request.form.get("input_type")
        extracted_text = ""

        if input_type == "URL":
            url = request.form.get("url")
            if not url:
                flash("Please enter a valid URL.")
                return redirect("/")
            extracted_text = extract_text_from_url(url)

        elif input_type == "PDF":
            file = request.files.get("pdf")
            if not file or file.filename == "":
                flash("Please upload a PDF file.")
                return redirect("/")
            ext = os.path.splitext(file.filename)[1].lower()
            if ext != ".pdf":
                flash("Only PDF files are supported.")
                return redirect("/")
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            text = extract_text(filepath, ext)
            if text is None:
                session['pdf_file'] = filepath
                session['pdf_ext'] = ext
                flash("PDF is password protected. Please enter the password.")
                return redirect("/password")

            extracted_text = text

        elif input_type == "Text":
            extracted_text = request.form.get("text", "").strip()
            if not extracted_text:
                flash("Please enter some text.")
                return redirect("/")

        if not extracted_text:
            flash("No text could be extracted.")
            return redirect("/")

        summary = summarize_text(extracted_text)
        return render_template("index.html", extracted_text=extracted_text, summary=summary)

    return render_template("index.html", extracted_text=None, summary=None)

@app.route("/password", methods=["GET", "POST"])
def password():
    if request.method == "POST":
        password = request.form.get("pdf_password")
        filepath = session.get("pdf_file")
        ext = session.get("pdf_ext")

        if not filepath or not os.path.exists(filepath):
            flash("File not found or session expired.")
            return redirect("/")

        text = extract_text(filepath, ext, password)
        if text is None:
            flash("Incorrect password. Please try again.")
            return redirect("/password")

        summary = summarize_text(text)
        return render_template("index.html", extracted_text=text, summary=summary)

    return render_template("password.html")
    
if __name__ == "__main__":
    app.run(debug=True)
