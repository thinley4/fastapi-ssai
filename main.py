from fastapi import FastAPI, Response
from pydantic import BaseModel
import uvicorn
from langchain_google_genai import ChatGoogleGenerativeAI
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestData(BaseModel):
    topic: str
    grade_level: int

key = os.getenv("key")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/process")
async def process_data(data: RequestData):
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        api_key=key,
    )
    
    prompt = f"""
    You are an AI assistant that generates structured worksheets for students.
    Generate a worksheet with a variety of question types (MCQs, short answers, and fill-in-the-blanks) 
    on the topic '{data.topic}' for Grade {data.grade_level} students.
    Ensure the questions are clear, engaging, and age-appropriate.
    
    Example Worksheet:

    **Topic: Fractions**
    **Grade: 5**

    1. **Multiple Choice Question:** What is 1/2 + 1/4?
       a) 3/4  
       b) 1/2  
       c) 2/4  
       d) 1  

    2. **Short Answer:** Explain the difference between proper and improper fractions.

    3. **Fill in the Blank:** 3/5 + __ = 1

    Now generate a worksheet based on the topic '{data.topic}' for Grade {data.grade_level} students.
    """

    ai_msg = llm.invoke(prompt)

    # Generate PDF
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter  # Get page dimensions

    c.setFont("Helvetica", 12)
    c.drawString(100, height - 50, f"Worksheet on {data.topic} (Grade {data.grade_level})")

    y_position = height - 70  # Start position below the title
    text_object = c.beginText(100, y_position)
    text_object.setFont("Helvetica", 12)

    max_width = width - 150  # Right margin buffer

    for line in ai_msg.content.split("\n"):
        words = line.split()
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if c.stringWidth(test_line, "Helvetica", 12) < max_width:
                current_line = test_line  # Add word if it fits
            else:
                text_object.textLine(current_line)  # Print current line
                current_line = word  # Start new line

        if current_line:
            text_object.textLine(current_line)  # Print last part of the line

        y_position -= 20
        if y_position < 50:  # If near bottom, start a new page
            c.drawText(text_object)
            c.showPage()
            y_position = height - 50
            text_object = c.beginText(100, y_position)
            text_object.setFont("Helvetica", 12)

    c.drawText(text_object)  # Draw the last text content
    c.save()
    pdf_buffer.seek(0)

    # Return PDF as a downloadable response
    return Response(content=pdf_buffer.getvalue(), media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=worksheet_{data.topic}.pdf"
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8880)