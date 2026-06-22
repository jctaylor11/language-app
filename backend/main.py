from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import vocab, sentences, dashboard

app = FastAPI()

origins = [
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(vocab.router)
app.include_router(sentences.router)
app.include_router(dashboard.router)




