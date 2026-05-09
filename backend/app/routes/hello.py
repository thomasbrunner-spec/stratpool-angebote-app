"""
Hello World endpoints — useful as templates and for sanity checks.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.auth import CurrentUser
from app.services.llm import simple_completion

router = APIRouter(prefix="/hello", tags=["hello"])


class HelloResponse(BaseModel):
    message: str


@router.get("/", response_model=HelloResponse)
async def hello_public() -> HelloResponse:
    """Public hello — no auth required."""
    return HelloResponse(message="Hello from Stratpool!")


@router.get("/me", response_model=HelloResponse)
async def hello_authenticated(user: CurrentUser) -> HelloResponse:
    """Authenticated hello — requires valid Supabase JWT."""
    email = user.email or "anonymous"
    return HelloResponse(message=f"Hello {email}, your user ID is {user.id}")


class HaikuRequest(BaseModel):
    topic: str = "the Stratpool platform"


class HaikuResponse(BaseModel):
    haiku: str
    topic: str


@router.post("/haiku", response_model=HaikuResponse)
async def hello_haiku(req: HaikuRequest, user: CurrentUser) -> HaikuResponse:
    """
    Demo endpoint: ask Claude to write a haiku.
    Requires auth so it cannot be abused publicly.
    """
    prompt = f"Write a haiku about: {req.topic}. Reply with only the haiku, no explanation."
    haiku = await simple_completion(prompt, max_tokens=100)
    return HaikuResponse(haiku=haiku.strip(), topic=req.topic)
