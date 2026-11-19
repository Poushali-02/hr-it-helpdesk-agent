"""Optional REST wrapper: uvicorn helpdesk.api:app"""
from fastapi import FastAPI
from pydantic import BaseModel

from .agent import ask as run

app = FastAPI(title="HR/IT Helpdesk Agent")


class AskRequest(BaseModel):
    question: str
    employee_id: str = "E102"


@app.post("/ask")
async def ask(req: AskRequest) -> dict:
    r = await run(req.question, req.employee_id)
    return {
        "answer": r.answer, "sources": r.sources, "tools_called": r.tools_called,
        "verdict": r.verdict, "latency_s": round(r.latency_s, 2),
    }
