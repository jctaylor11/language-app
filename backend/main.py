from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import auth, session, sentence, vocab, dashboard
from backend.config import FRONTEND_ORIGIN

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(session.router)
app.include_router(vocab.router)
app.include_router(sentence.router)
app.include_router(dashboard.router)
app.include_router(auth.router)




