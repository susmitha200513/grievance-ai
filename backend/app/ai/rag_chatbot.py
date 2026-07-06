"""
RAG-based citizen assistant. Loads .txt/.md documents from docs_kb/,
embeds and stores them in a local Chroma vector store, and answers
citizen questions using retrieval-augmented generation.

Falls back to plain keyword search over the same documents if no
GOOGLE_API_KEY is set, so the chatbot still returns something useful
in a demo without a key.
"""
import os
import glob
from typing import Tuple, List

from app.config import settings

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs_kb")
_vectorstore = None


def _load_documents() -> List[str]:
    texts = []
    for path in glob.glob(os.path.join(DOCS_DIR, "*.*")):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            texts.append((os.path.basename(path), f.read()))
    return texts


def _get_vectorstore():
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from langchain_community.vectorstores import Chroma
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.docstore.document import Document

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = []
    for fname, text in _load_documents():
        for chunk in splitter.split_text(text):
            docs.append(Document(page_content=chunk, metadata={"source": fname}))

    if not docs:
        return None

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004", google_api_key=settings.GOOGLE_API_KEY
    )
    _vectorstore = Chroma.from_documents(docs, embeddings)
    return _vectorstore


def _keyword_fallback(question: str) -> Tuple[str, List[str]]:
    q_words = set(question.lower().split())
    best_fname, best_text, best_overlap = None, "", 0
    for fname, text in _load_documents():
        for para in text.split("\n\n"):
            overlap = len(q_words & set(para.lower().split()))
            if overlap > best_overlap:
                best_overlap = overlap
                best_text = para.strip()
                best_fname = fname

    if best_text:
        return (
            f"Based on our records: {best_text}",
            [best_fname],
        )
    return (
        "I couldn't find that in our knowledge base yet. Please contact your local "
        "municipal office, or file a complaint and an officer will respond.",
        [],
    )


def answer_question(question: str) -> Tuple[str, List[str]]:
    if not settings.GOOGLE_API_KEY:
        return _keyword_fallback(question)

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        vectorstore = _get_vectorstore()
        if vectorstore is None:
            return _keyword_fallback(question)

        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        relevant_docs = retriever.invoke(question)
        context = "\n\n".join(d.page_content for d in relevant_docs)
        sources = list({d.metadata.get("source", "unknown") for d in relevant_docs})

        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0, google_api_key=settings.GOOGLE_API_KEY)
        prompt = (
            "You are a helpful citizen assistant for a municipal grievance portal. "
            "Answer the question using ONLY the context below. If the answer isn't "
            "in the context, say you don't have that information and suggest filing "
            "a complaint or contacting the municipal office.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        )
        response = llm.invoke(prompt)
        return response.content.strip(), sources
    except Exception:
        return _keyword_fallback(question)
