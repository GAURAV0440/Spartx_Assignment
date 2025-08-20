from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
import os
import openai

# Load env variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

# Configure OpenAI client (works for Groq)
openai.api_key = GROQ_API_KEY
openai.api_base = "https://api.groq.com/openai/v1"

# FastAPI setup
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory storage for generated SOP
SOP_STORAGE = {}

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate-sop", response_class=JSONResponse)
async def generate_sop(
    full_name: str = Form(...),
    age: str = Form(...),
    country: str = Form(...),
    course: str = Form(...),
    university: str = Form(...),
    education: str = Form(...),
    goals: str = Form(...)
):
    # Prompt construction
    prompt = f"""
Write a concise and professional Statement of Purpose (SOP) for a student visa application using the following details:

Name: {full_name}
Age: {age}
Country Applying To: {country}
Desired Course: {course}
University: {university}
Educational Background: {education}
Future Goals: {goals}

The SOP should:
- Be formal and persuasive
- Cover academic background, motivation, goals, and why the applicant chose this country and university
- Be limited to around 500 words
- Avoid unnecessary repetition

Start directly and keep the writing compact but impressive.
"""

    try:
        response = openai.ChatCompletion.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an expert SOP writer for student visa applications."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=700
        )

        generated_text = response.choices[0].message.content.strip()
        SOP_STORAGE["latest"] = generated_text

        print(" Groq response received.")
        return {"sop": generated_text}

    except Exception as e:
        print(" Error from Groq API:", str(e))
        return {"error": "Failed to generate SOP. Please check your API key, model name, or usage limits."}


@app.post("/save-sop")
async def save_sop(content: str = Form(...)):
    SOP_STORAGE["latest"] = content
    return {"message": "SOP saved for PDF download."}


@app.get("/download-pdf")
async def download_pdf():
    sop_text = SOP_STORAGE.get("latest", "No SOP found.")
    pdf_path = "sop_output.pdf"

    c = canvas.Canvas(pdf_path, pagesize=LETTER)
    width, height = LETTER
    lines = sop_text.split("\n")
    y = height - 50

    for line in lines:
        c.drawString(50, y, line)
        y -= 15
        if y < 50:
            c.showPage()
            y = height - 50

    c.save()
    return FileResponse(pdf_path, filename="SOP.pdf", media_type="application/pdf")
