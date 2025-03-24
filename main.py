from fastapi import FastAPI, Response
from pydantic import BaseModel
import uvicorn
from langchain_google_genai import ChatGoogleGenerativeAI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
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

    # Correcting the prompt format
    messages = [
        (
            "system",
            """You are an AI assistant that generates structured worksheets for students. 
            Generate a worksheet in **Markdown format** with a variety of question types 
            (MCQs, short answers, and fill-in-the-blanks) on the topic **'{topic}'** 
            for **Grade {grade_level}** students. 

            Ensure:
            - Questions are clear, engaging, and age-appropriate.
            - Use proper markdown formatting for better readability.

            Example Markdown Format:
            ```
            # Topic: Fractions
            ## Grade: 5

            ### 1. Multiple Choice Question:
            **What is 1/2 + 1/4?**
            - a) 3/4  
            - b) 1/2  
            - c) 2/4  
            - d) 1  

            ### 2. Short Answer:
            **Explain the difference between proper and improper fractions.**

            ### 3. Fill in the Blank:
            **3/5 + __ = 1**
            ```

            Now generate a worksheet in markdown format.
            """,
        ),
        ("human", f"Generate a worksheet on {data.topic} for Grade {data.grade_level}."),
    ]

    ai_msg = llm.invoke(messages)

    return {"worksheet": ai_msg.content}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8880)
