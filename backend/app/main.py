from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers import auth_routes, complaints, dashboard, officers, chatbot

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Grievance Resolution & Constituency Intelligence Engine",
    description="AI-powered grievance system using LangChain and RAG",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this before any real deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth_routes.router)
app.include_router(complaints.router)
app.include_router(dashboard.router)
app.include_router(officers.router)
app.include_router(chatbot.router)


@app.get("/")
def root():
    return {"message": "Grievance AI backend is running", "docs": "/docs"}
