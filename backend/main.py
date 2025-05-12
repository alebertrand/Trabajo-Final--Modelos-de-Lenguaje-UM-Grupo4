from fastapi import FastAPI
from pydantic import BaseModel
from backend.rag_pipeline import RAGPipeline
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
rag = RAGPipeline()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

@app.post("/ask")
def ask_question(payload: QuestionRequest):
    answer = rag.ask(payload.question)
    return {"answer": answer}