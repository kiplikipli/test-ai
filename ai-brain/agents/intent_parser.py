from datetime import datetime
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from config import settings


class ParsedIntent(BaseModel):
    intent: Literal['collect_details', 'resolve_attendees', 'schedule', 'confirm', 'modify', 'unknown']
    title: str | None = None
    duration_minutes: int | None = None
    attendee_names: list[str] = Field(default_factory=list)
    date_start: datetime | None = None
    date_end: datetime | None = None
    timezone: str | None = None
    confirmation: bool = False


_llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
    temperature=0,
)

_prompt = ChatPromptTemplate.from_messages(
    [
        ('system', 'Extract only explicit scheduling intent updates. Never invent values.'),
        ('human', 'Message: {message}'),
    ]
)


async def parse_intent(message: str) -> ParsedIntent:
    structured = _llm.with_structured_output(ParsedIntent)
    chain = _prompt | structured
    return await chain.ainvoke({'message': message})
