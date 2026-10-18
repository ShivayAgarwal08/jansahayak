from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.assistant import AssistantChatRequest, AssistantChatResponse
from app.services.rag.retrieval import retrieve_grounded_passages
from app.services.ai.groq_service import generate_grounded_answer

router = APIRouter(prefix="/assistant", tags=["Assistant & RAG"])

@router.post("/chat", response_model=AssistantChatResponse)
async def chat_with_assistant(
    req: AssistantChatRequest,
    db: Session = Depends(get_db)
):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # 1. Retrieve top verified passages
    passages = retrieve_grounded_passages(query, db, limit=4)

    # 2. Generate grounded answer
    result = await generate_grounded_answer(
        query=query,
        passages=passages,
        preferred_language=req.preferred_language
    )

    return result
