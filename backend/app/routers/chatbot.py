from fastapi import APIRouter, Depends

from app import auth, models, schemas
from app.ai import rag_chatbot

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.post("/ask", response_model=schemas.ChatResponse)
def ask(
    payload: schemas.ChatQuery,
    current_user: models.User = Depends(auth.get_current_user),
):
    answer, sources = rag_chatbot.answer_question(payload.question)
    return schemas.ChatResponse(answer=answer, sources=sources)
