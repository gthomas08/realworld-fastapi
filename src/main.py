from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from src.auth.router import auth_router
from src.users.router import router as users_router
from src.profiles.router import router as profiles_router
from src.tags.router import router as tags_router
from src.articles.router import router as articles_router
from src.comments.router import router as comments_router


app = FastAPI(
    title="Real World FastAPI",
    description="A Medium-like clone backend API built with FastAPI.",
)

# Optionally add CORS middleware (customize as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(profiles_router)
app.include_router(tags_router)
app.include_router(articles_router)
app.include_router(comments_router)


@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )
